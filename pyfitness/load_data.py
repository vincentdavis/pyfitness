import warnings
from datetime import datetime
from typing import Any

warnings.simplefilter(action='ignore', category=FutureWarning)

import fitdecode
import pandas as pd

pd.set_option('mode.chained_assignment', None)


def slots2dict(classobj: object) -> dict:
    "Convert a class object with slots to a dict"
    # {s: getattr(classobj, s, None) for s in classobj.__slots__}
    return {s: getattr(classobj, s, None) for s in classobj.__slots__ if 'unknown_' not in s}


def FieldDefinition2dict(frame: fitdecode.records.FitDefinitionMessage) -> dict:
    "Convert a FieldDefinition to dict"
    frame_dict = {}
    for d in frame.field_defs:
        if 'unknown_' in d.name.lower():
            continue
        frame_dict['name'] = d.name
        frame_dict['is_dev'] = d.is_dev
        frame_dict['type']: d.type.name
    return frame_dict

    # return {s: getattr(FieldDefinition, s, None) for s in FieldDefinition.__slots__}


def frame2dict(frame: fitdecode.records.FitDataMessage) -> dict:
    "Convert a fonvert frame fields to dict"
    frame_dict = {}
    for field in frame.fields:
        # print(f"Frame Field Name: {field.value}")
        if 'unknown_' in field.name.lower():
            continue
        try:
            frame_dict[field.name] = frame.get_value(field.name)
        except KeyError:
            frame_dict[field.name] = None
    return frame_dict


def fit2dict(fit_file: str | bytes, from_file=True) -> dict[str, None | dict | list[dict] | set[Any]]:
    """Load a fit file"""
    header = None
    definitions = []
    other_records = []
    events = []
    sessions = []
    activity = None
    records = []
    crcs = None
    other = []
    # def process(fit):
    fit = fitdecode.FitReader(fit_file)
    event = dict()
    columns = set()
    for i, frame in enumerate(fit):
        match frame:
            case fitdecode.records.FitHeader():
                header = (slots2dict(frame))
            case fitdecode.records.FitDefinitionMessage():
                definitions.append(FieldDefinition2dict(frame))
            case fitdecode.records.FitDataMessage():
                if 'unknown_' not in frame.name.lower():
                    match frame.name:
                        case 'event':
                            event = frame2dict(frame)
                            events.append(event)
                        case 'session':
                            sessions.append(frame2dict(frame))
                        case 'activity':
                            activity = frame2dict(frame)
                        case 'record':
                            rec = frame2dict(frame)
                            # rec.update(event)
                            columns.update(rec.keys())
                            records.append(rec)
                        case _:
                            other_records.append(frame2dict(frame))
            case fitdecode.records.FitCRC():
                crcs = slots2dict(frame)
            case _:
                other.append(slots2dict(frame))
    fit_dict = {'header': header, 'definitions': definitions, 'events': events, 'sessions': sessions,
                'activity': activity,
                'other_records': other_records, 'records': records, 'crcs': crcs, 'other': other, 'columns': columns}
    return fit_dict


def fit2df(fit_file: str) -> pd.DataFrame:
    """Load a fit file into a pandas dataframe"""
    fit_dict = fit2dict(fit_file)
    # df = pd.DataFrame(columns=list(fit_dict['columns']))
    df = pd.DataFrame.from_dict(fit_dict['records'])
    df.set_index('timestamp', inplace=True)
    df.dropna(how='all', axis='columns', inplace=True)
    df.dropna(how='all', axis='index', inplace=True)
    return df


def fit2csv(fitfile: str | pd.DataFrame, outfile=None):
    if isinstance(fitfile, str):
        df = fit2df(fitfile)
    elif isinstance(fitfile, pd.DataFrame):
        df = fitfile
    # deal with timezone columns in FitDataMessages_df
    try:
        date_columns = df.select_dtypes(include=['datetime64[ns, UTC]']).columns
    except:
        date_columns = []

    for c in date_columns:
        try:
            df[c] = df[c].apply(
                lambda a: datetime.strftime(a, "%Y-%m-%d %H:%M:%S") if not pd.isnull(a) else '')
        except:
            raise
    if outfile:
        return df.to_csv(outfile)
    else:
        return df.to_csv().encode('utf-8')


def fit2excel(fitfile, outfile=None):
    df = fit2df(fitfile)
    date_columns = df.select_dtypes(include=['datetime64[ns, UTC]']).columns
    for c in date_columns:
        try:
            df[c] = df[c].apply(
                lambda a: datetime.strftime(a, "%Y-%m-%d %H:%M:%S") if not pd.isnull(a) else '')
        except:
            raise
    if outfile:
        return df.to_excel(outfile)
    else:
        return df.to_excel().encode('utf-8')


def fitfileinfo(fit, show_unkown=False):
    "Creates a MarkDown text file object with information about the fit file"
    if fit.__class__ == fitdecode.reader.FitReader:
        pass
    else:
        fit = fitdecode.FitReader(fit)
    records = 0
    record_fields = set()
    events = 0
    event_types = set()
    sessions = 0
    activitys = 0
    laps = 0
    fileinfo = "# Fit File details\n\n"
    for d in fit:
        match d:
            case fitdecode.records.FitHeader():
                fileinfo += f"### Header:\n"
                for k, v in slots2dict(d).items():
                    fileinfo += f"- {k}: {v}\n"
            case fitdecode.records.FitDataMessage():
                records += 1 if d.name == 'record' else 0
                events += 1 if d.name == 'event' else 0
                sessions += 1 if d.name == 'session' else 0
                activitys += 1 if d.name == 'activity' else 0
                laps += 1 if d.name == 'lap' else 0
                if d.name == 'record':
                    record_fields.update(frame2dict(d).keys())
                if d.name.lower() not in ['record', 'event', 'session', 'activity', 'lap']:
                    if show_unkown or "unknown_" not in d.name.lower():
                        fileinfo += f"### Data type: {d.name.upper()}\n"
                        for field in d.fields:
                            if show_unkown or "unknown_" not in field.name.lower():
                                fileinfo += f"- {field.name}: {field.value}\n"
                if d.name == 'activity':
                    fileinfo += f"### activity\n"
                    for k, v in frame2dict(d).items():
                        fileinfo += f"- {k}: {v}\n"
                if d.name == 'session':
                    fileinfo += f"### session\n"
                    for k, v in frame2dict(d).items():
                        fileinfo += f"- {k}: {v}\n"
                if d.name == 'lap':
                    fileinfo += f"### lap\n"
                    for k, v in frame2dict(d).items():
                        fileinfo += f"- {k}: {v}\n"
                if d.name == 'event':
                    event_types.add(d.get_value('event'))

    fileinfo += f"### Data Records:\n" \
                f"- records: {records}\n" \
                f"- events: {events}\n" \
                f"- sessions: {sessions}\n" \
                f"- activitys: {activitys}\n" \
                f"- laps: {laps}\n"
    fileinfo += f"###Record Fields:\n"
    for field in record_fields:
        fileinfo += f"- {field}\n"
    fileinfo += f"###Event Types:\n"
    for etype in event_types:
        fileinfo += f"- {etype}\n"
    return fileinfo