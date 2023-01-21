from math import exp, radians

import numpy as np
import pandas as pd


def max_climb(df: pd.DataFrame, seconds: int) -> dict[str, int, int, float, float]:
    """Find the max elevation gain for the given time period
    Assumes a column named seconds exists in the dataframe
    """
    try:
        assert('altitude' in df.columns or 'enhanced_altitude' in df.columns)
        if 'enhanced_altitude' in df.columns:
            altitudevar = 'enhanced_altitude'
        else:
            altitudevar = 'altitude'
        assert (all([c in df.columns for c in ['seconds', 'distance']]))
    except AssertionError:
        print(f"{df.columns}")
        raise AssertionError("Missing columns in dataframe. Must have 'seconds', 'distance', and 'altitude'")
    try:
        assert (df.seconds.max() - df.seconds.min() > seconds)
    except AssertionError:
        raise AssertionError("Time period is longer than the activity")
    try:
        assert (df.distance.max() - df.distance.min() > 0)
    except AssertionError:
        raise AssertionError("Distance is 0 in data.")
    end_time, end_distance = df.loc[df[altitudevar].diff(seconds).idxmax(), ['seconds', 'distance']].values
    start_time = end_time - seconds
    start_distance = df.loc[df['seconds'] == start_time, 'distance'].values
    end_distance = df.loc[df['seconds'] + seconds == start_time, 'distance'].values
    p = ''
    p += f"{seconds / 60}min: {int(df[altitudevar].diff(seconds).max())}m elevation gain over {int(end_distance - start_distance)}m\n"
    p += f"-- Starting at {int(end_time - seconds)}sec,  start_distance: {int(start_distance)}m\n"
    p += f"-- Ending at {int(end_time)}sec, end_distance: {int(end_distance)}m"
    return {'text': p, 'start_time': start_time, 'end_time': end_time, 'start_distance': start_distance,
            'end_distance': end_distance}


def simulator(df: pd.DataFrame, rider_weight: float, bike_weight: float, wind_speed: float, wind_direction: int,
              temperature: float, drag_coefficient: float, frontal_area: float, rolling_resistance: float,
              efficiency_loss: float, speedcol: str = None, altitudecol: str = None) -> pd.DataFrame:
    """Estimate power output based on the given parameters"""
    try:
        assert (all([c in df.columns for c in ['distance', 'altitude']]) or
                all([c in df.columns for c in ['distance', 'enhanced_altitude']]))
    except AssertionError:
        # print(f"{df.columns}")
        raise AssertionError(f"Missing columns in dataframe. Must have 'seconds', 'distance', and 'altitude'")
    # Use the best Altitude data.
    if 'enhanced_altitude' in df.columns:
        altitudevar = 'enhanced_altitude'
    else:
        altitudevar = 'altitude'
    # Use the best speed data
    if "enhanced_speed" in df.columns:
        speedvar = "enhanced_speed"
    elif "speed" in df.columns:
        speedvar = "speed"
    else:  # or calculate speed
        df['speed_calculated'] = df.distance.diff() / df.time.diff()
        speedvar = "speed_calculated"
    # User set speed and altitude. This could be any col in the df
    if altitudecol is not None:
        assert (altitudecol in df.columns)
        altitudevar = altitudecol
    if speedcol is not None:
        assert (speedcol in df.columns)
        speedvar = speedcol

    # # create a seconds based col starting at 0
    # # This is used for to select the start and end time
    if 'seconds' not in df.columns:
        df['seconds'] = pd.to_datetime(df.index, unit='s', origin='unix').astype(int) // 10 ** 9
        df['seconds'] = df['seconds'] - df.seconds.min()

    df['vam'] = (df[altitudevar].diff() / df.seconds.diff()) * 3600
    df['slope'] = df[altitudevar].diff() / df.distance.diff()

    # # Constants
    CdA = drag_coefficient * frontal_area
    altitude = (df.altitude.max() - df.altitude.min()) / 2
    # intermediate calculations
    df['air_density'] = ((101325 / (287.05 * 273.15)) * (273.15 / (temperature + 273.15)) *
                         exp((-101325 / (287.05 * 273.15)) * 9.8067 * (altitude / 101325)))
    df['effective_wind_speed'] = np.cos(radians(wind_direction)) * wind_speed
    # # Components of power, watts
    df['air_drag_watts'] = 0.5 * CdA * df.air_density * np.square(df[speedvar] + df.effective_wind_speed) * df[speedvar]
    df['climbing_watts'] = (bike_weight + rider_weight) * 9.8067 * np.sin(np.arctan(df.slope)) * df[speedvar]
    df['rolling_watts'] = np.cos(np.arctan(df.slope)) * 9.8067 * (
            bike_weight + rider_weight) * rolling_resistance * df[speedvar]
    df['acceleration_watts'] = (bike_weight + rider_weight) * (df[speedvar].diff() / df.seconds.diff()) * df[speedvar]
    df['est_power_no_loss'] = df[['air_drag_watts', 'climbing_watts', 'rolling_watts', 'acceleration_watts']].sum(
        axis='columns')
    df['est_power'] = df['est_power_no_loss'] / (1 - efficiency_loss)
    df['efficiency_loss_watts'] = df['est_power_no_loss'] - df['est_power']
    df['est_power_no_acc'] = (df['est_power_no_loss'] - df['acceleration_watts']) / (1 - efficiency_loss)
    return df


def climb_power_eestimate(df: pd.DataFrame, rider_weight: float, bike_weight: float, wind_speed: float,
                          wind_direction: int,
                          temperature: float, drag_coefficient: float, frontal_area: float, rolling_resistance: float,
                          efficiency_loss: float) -> dict[int, float, ...]:
    """Find the average estimated power for the given time period
    We assume the df is filtered to the area of interest"""
    elapsed_time = df.seconds.max() - df.seconds.min()
    distance = df.distance.max() - df.distance.min()
    accent = df.altitude.max() - df.altitude.min()
    slope = accent / distance
    speed = distance / elapsed_time
    speed_kph = speed * 3.6
    avg_elevation = df.altitude.mean()
    CdA = drag_coefficient * frontal_area

    air_density = ((101325 / (287.05 * 273.15)) * (273.15 / (temperature + 273.15)) *
                   exp((-101325 / (287.05 * 273.15)) * 9.8067 * (avg_elevation / 1013.25)))
    effective_wind_speed = np.cos(radians(wind_direction)) * wind_speed
    # # Components of power, watts
    air_drag_watts = 0.5 * CdA * air_density * (speed + effective_wind_speed) ** 2 * speed
    climbing_watts = (bike_weight + rider_weight) * 9.8067 * np.sin(np.arctan(slope)) * speed
    rolling_watts = np.cos(np.arctan(slope)) * 9.8067 * (
            bike_weight + rider_weight) * rolling_resistance * speed
    est_power_no_loss = sum([air_drag_watts, climbing_watts, rolling_watts])
    est_power = est_power_no_loss / (1 - efficiency_loss)
    vam_mhr = (accent / elapsed_time) * 3600

    return {'elapsed_time': elapsed_time, 'distance': distance, 'accent': accent, 'slope': slope, 'speed': speed,
            'speed_kph': speed_kph, 'avg_elevation': avg_elevation, 'frontal_area': frontal_area,
            'drag_coefficient': drag_coefficient, 'CdA': CdA, 'air_density': air_density,
            'effective_wind_speed': effective_wind_speed,
            'air_drag_watts': air_drag_watts, 'climbing_watts': climbing_watts, 'rolling_watts': rolling_watts,
            'vam_mhr': vam_mhr, 'est_power_no_loss': est_power_no_loss, 'est_power': est_power}
