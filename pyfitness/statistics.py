import pandas as pd


def max_climb(df: pd.DataFrame, seconds: int) -> dict[str, int, int, float, float]:
    """Find the max elevation gain for the given time period
    Assumes a column named seconds exists in the dataframe
    """
    try:
        assert ('altitude' in df.columns or 'enhanced_altitude' in df.columns)
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
