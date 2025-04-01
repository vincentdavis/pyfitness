"""
This loader uses the Garmin SDK to load the data from the FIT file.
https://developer.garmin.com/fit/example-projects/python/
"""

from garmin_fit_sdk import Decoder, Stream, Profile


record_fields = set()
profile_types = set()


def mesg_listener(mesg_num, message):
    profile_types.add(mesg_num)
    if mesg_num == Profile["mesg_num"]["RECORD"]:
        for field in message:
            record_fields.add(field)


def fit2dict(fit_file: str):
    stream = Stream.from_file(fit_file)
    decoder = Decoder(stream)
    # loop through the messages
    messages, errors = decoder.read(mesg_listener=mesg_listener)

    if len(errors) > 0:
        print(f"Something went wrong decoding the file: {errors}")
        return

    print(record_fields)
    print(profile_types)


if __name__ == "__main__":
    fit2dict("../tests/testdata/outdoor/Morning_Ride.fit")
