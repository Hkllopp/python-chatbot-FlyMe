# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


class BookingDetails:
    def __init__(
        self,
        destination: str = None,
        origin: str = None,
        max_budget: int = None,
        travel_date: str = None,
        travel_back_date: str = None,
        unsupported_airports=None,
    ):
        if unsupported_airports is None:
            unsupported_airports = []
        self.destination = destination
        self.origin = origin
        self.max_budget = max_budget
        self.travel_date = travel_date
        self.travel_back_date = travel_back_date
        self.unsupported_airports = unsupported_airports
