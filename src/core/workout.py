"""
Workout management and execution
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
from loguru import logger

from .models import PowerData, TrainingSession


class WorkoutType(Enum):
    STEADY_STATE = "steady_state"
    INTERVALS = "intervals"
    TEMPO = "tempo"
    SPRINT = "sprint"
    CUSTOM = "custom"


@dataclass
class WorkoutInterval:
    """A single interval within a workout"""
    duration_seconds: int
    target_power: int
    target_cadence: Optional[int] = None
    description: str = ""
    rest_seconds: int = 0  # Rest between intervals
    
    def __post_init__(self):
        if not self.description:
            self.description = f"{self.duration_seconds}s @ {self.target_power}W"


@dataclass
class Workout:
    """Complete workout definition"""
    name: str
    description: str
    workout_type: WorkoutType
    intervals: List[WorkoutInterval]
    warmup_duration: int = 300  # 5 minutes default
    cooldown_duration: int = 300  # 5 minutes default
    
    def __post_init__(self):
        self.total_duration = sum(interval.duration_seconds + interval.rest_seconds for interval in self.intervals)
        self.total_duration += self.warmup_duration + self.cooldown_duration


class WorkoutExecutor:
    """Executes workouts and provides guidance"""
    
    def __init__(self):
        self.current_workout: Optional[Workout] = None
        self.current_interval_index: int = 0
        self.interval_start_time: Optional[datetime] = None
        self.workout_start_time: Optional[datetime] = None
        self.phase: str = "idle"  # idle, warmup, interval, rest, cooldown
        self.callbacks: List[callable] = []
        
    def add_callback(self, callback: callable):
        """Add callback for workout events"""
        self.callbacks.append(callback)
        
    def _notify_callbacks(self, event_type: str, data: Dict[str, Any]):
        """Notify all callbacks of workout events"""
        for callback in self.callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                logger.error(f"Error in workout callback: {e}")
    
    def start_workout(self, workout: Workout):
        """Start executing a workout"""
        self.current_workout = workout
        self.current_interval_index = 0
        self.workout_start_time = datetime.now()
        self.phase = "warmup"
        self.interval_start_time = self.workout_start_time
        
        logger.info(f"Started workout: {workout.name}")
        self._notify_callbacks("workout_started", {
            "workout": workout,
            "phase": self.phase,
            "remaining_time": workout.warmup_duration
        })
    
    def update(self, current_power: PowerData) -> Dict[str, Any]:
        """Update workout state based on current power data"""
        if not self.current_workout:
            return {}
            
        now = datetime.now()
        elapsed = (now - self.interval_start_time).total_seconds()
        
        guidance = {
            "phase": self.phase,
            "elapsed_time": elapsed,
            "remaining_time": 0,
            "target_power": 0,
            "target_cadence": None,
            "description": "",
            "power_difference": 0,
            "guidance": ""
        }
        
        if self.phase == "warmup":
            guidance["remaining_time"] = self.current_workout.warmup_duration - elapsed
            guidance["target_power"] = int(current_power.instantaneous_power * 0.5)  # 50% of current
            guidance["description"] = "Warmup"
            
            if elapsed >= self.current_workout.warmup_duration:
                self._start_next_interval()
                
        elif self.phase == "interval":
            interval = self.current_workout.intervals[self.current_interval_index]
            guidance["remaining_time"] = interval.duration_seconds - elapsed
            guidance["target_power"] = interval.target_power
            guidance["target_cadence"] = interval.target_cadence
            guidance["description"] = interval.description
            guidance["power_difference"] = current_power.instantaneous_power - interval.target_power
            
            # Provide guidance
            if guidance["power_difference"] > 20:
                guidance["guidance"] = "Reduce power slightly"
            elif guidance["power_difference"] < -20:
                guidance["guidance"] = "Increase power"
            else:
                guidance["guidance"] = "Good power!"
                
            if elapsed >= interval.duration_seconds:
                self._finish_interval()
                
        elif self.phase == "rest":
            interval = self.current_workout.intervals[self.current_interval_index - 1]
            guidance["remaining_time"] = interval.rest_seconds - elapsed
            guidance["target_power"] = int(current_power.instantaneous_power * 0.3)  # 30% of current
            guidance["description"] = "Rest"
            
            if elapsed >= interval.rest_seconds:
                self._start_next_interval()
                
        elif self.phase == "cooldown":
            guidance["remaining_time"] = self.current_workout.cooldown_duration - elapsed
            guidance["target_power"] = int(current_power.instantaneous_power * 0.4)  # 40% of current
            guidance["description"] = "Cooldown"
            
            if elapsed >= self.current_workout.cooldown_duration:
                self._finish_workout()
        
        return guidance
    
    def _start_next_interval(self):
        """Start the next interval"""
        if self.current_interval_index < len(self.current_workout.intervals):
            self.phase = "interval"
            self.interval_start_time = datetime.now()
            interval = self.current_workout.intervals[self.current_interval_index]
            
            logger.info(f"Starting interval {self.current_interval_index + 1}: {interval.description}")
            self._notify_callbacks("interval_started", {
                "interval_index": self.current_interval_index,
                "interval": interval,
                "phase": self.phase
            })
        else:
            self._start_cooldown()
    
    def _finish_interval(self):
        """Finish current interval and start rest or next interval"""
        interval = self.current_workout.intervals[self.current_interval_index]
        self.current_interval_index += 1
        
        if interval.rest_seconds > 0 and self.current_interval_index < len(self.current_workout.intervals):
            self.phase = "rest"
            self.interval_start_time = datetime.now()
            logger.info(f"Rest period: {interval.rest_seconds}s")
            self._notify_callbacks("rest_started", {
                "rest_duration": interval.rest_seconds,
                "phase": self.phase
            })
        else:
            self._start_next_interval()
    
    def _start_cooldown(self):
        """Start cooldown phase"""
        self.phase = "cooldown"
        self.interval_start_time = datetime.now()
        logger.info("Starting cooldown")
        self._notify_callbacks("cooldown_started", {
            "phase": self.phase,
            "duration": self.current_workout.cooldown_duration
        })
    
    def _finish_workout(self):
        """Finish the workout"""
        self.phase = "completed"
        total_time = (datetime.now() - self.workout_start_time).total_seconds()
        
        logger.info(f"Workout completed in {total_time:.1f} seconds")
        self._notify_callbacks("workout_completed", {
            "phase": self.phase,
            "total_time": total_time,
            "workout": self.current_workout
        })
        
        self.current_workout = None
        self.current_interval_index = 0
        self.workout_start_time = None
        self.interval_start_time = None
    
    def stop_workout(self):
        """Stop the current workout"""
        if self.current_workout:
            logger.info("Workout stopped by user")
            self._notify_callbacks("workout_stopped", {
                "phase": self.phase,
                "workout": self.current_workout
            })
            
            self.current_workout = None
            self.current_interval_index = 0
            self.workout_start_time = None
            self.interval_start_time = None
            self.phase = "idle"


# Predefined workouts
def create_steady_state_workout(duration_minutes: int, power_watts: int) -> Workout:
    """Create a steady state workout"""
    return Workout(
        name=f"Steady State {duration_minutes}min",
        description=f"Steady state ride at {power_watts}W for {duration_minutes} minutes",
        workout_type=WorkoutType.STEADY_STATE,
        intervals=[
            WorkoutInterval(
                duration_seconds=duration_minutes * 60,
                target_power=power_watts,
                description=f"Steady state at {power_watts}W"
            )
        ]
    )


def create_interval_workout(work_seconds: int, rest_seconds: int, 
                          work_power: int, rest_power: int, 
                          repetitions: int) -> Workout:
    """Create an interval workout"""
    intervals = []
    for i in range(repetitions):
        intervals.append(WorkoutInterval(
            duration_seconds=work_seconds,
            target_power=work_power,
            description=f"Work interval {i+1}/{repetitions}",
            rest_seconds=rest_seconds if i < repetitions - 1 else 0
        ))
    
    return Workout(
        name=f"Intervals {repetitions}x{work_seconds}s",
        description=f"{repetitions} intervals of {work_seconds}s work, {rest_seconds}s rest",
        workout_type=WorkoutType.INTERVALS,
        intervals=intervals
    )


def create_tempo_workout(duration_minutes: int, power_watts: int) -> Workout:
    """Create a tempo workout"""
    return Workout(
        name=f"Tempo {duration_minutes}min",
        description=f"Tempo ride at {power_watts}W for {duration_minutes} minutes",
        workout_type=WorkoutType.TEMPO,
        intervals=[
            WorkoutInterval(
                duration_seconds=duration_minutes * 60,
                target_power=power_watts,
                target_cadence=90,
                description=f"Tempo at {power_watts}W, 90 RPM"
            )
        ]
    )
