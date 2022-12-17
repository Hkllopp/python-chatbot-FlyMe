# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Flight booking dialog."""

from datatypes_date_time.timex import Timex

from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.dialogs.prompts import (
    ConfirmPrompt,
    TextPrompt,
    PromptOptions,
)
from botbuilder.core import MessageFactory, BotTelemetryClient, NullTelemetryClient
from .cancel_and_help_dialog import CancelAndHelpDialog
from .date_resolver_dialog import DateResolverDialog


class BookingDialog(CancelAndHelpDialog):
    """Flight booking implementation."""

    def __init__(
        self,
        dialog_id: str = None,
        telemetry_client: BotTelemetryClient = NullTelemetryClient(),
    ):
        super(BookingDialog, self).__init__(
            dialog_id or BookingDialog.__name__, telemetry_client
        )
        self.dialog_id = dialog_id
        self.telemetry_client = telemetry_client
        text_prompt = TextPrompt(TextPrompt.__name__)
        text_prompt.telemetry_client = telemetry_client

        waterfall_dialog = WaterfallDialog(
            WaterfallDialog.__name__,
            [
                self.destination_step,
                self.origin_step,
                self.max_budget_step,
                self.travel_date_step,
                self.travel_back_date_step,
                self.confirm_step,
                self.final_step,
            ],
        )
        waterfall_dialog.telemetry_client = telemetry_client

        self.add_dialog(text_prompt)
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(
            DateResolverDialog("departureDateDialogue", self.telemetry_client)
        )
        self.add_dialog(
            DateResolverDialog(
                "returnDateDialogue",
                self.telemetry_client,
                message="When would you like to return?",
            )
        )
        self.add_dialog(waterfall_dialog)

        self.initial_dialog_id = WaterfallDialog.__name__

    async def destination_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for destination."""
        booking_details = step_context.options

        if booking_details.destination is None:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("To what city would you like to travel?")
                ),
            )  # pylint: disable=line-too-long,bad-continuation

        return await step_context.next(booking_details.destination)

    async def origin_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt for origin city."""
        booking_details = step_context.options

        # Capture the response to the previous step's prompt
        booking_details.destination = step_context.result
        if booking_details.origin is None:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("From what city will you be travelling?")
                ),
            )  # pylint: disable=line-too-long,bad-continuation

        return await step_context.next(booking_details.origin)

    async def max_budget_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for max budget."""
        booking_details = step_context.options

        # Capture the results of the previous step
        booking_details.origin = step_context.result
        if booking_details.max_budget is None:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text(
                        "What is your maximum budget for the trip?"
                    ),
                ),
            )

        return await step_context.next(booking_details.max_budget)

    async def travel_date_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for travel date.
        This will use the DATE_RESOLVER_DIALOG."""

        booking_details = step_context.options

        # Capture the results of the previous step
        booking_details.max_budget = step_context.result

        # If max_budget not castable to int, send warning message
        if not booking_details.max_budget.isdigit():
            await step_context.context.send_activity(
                "Be careful, your budget is most likely not a number!"
            )

        if not booking_details.travel_date or self.is_ambiguous(
            booking_details.travel_date
        ):
            return await step_context.begin_dialog(
                "departureDateDialogue", booking_details.travel_date
            )  # pylint: disable=line-too-long

        return await step_context.next(booking_details.travel_date)

    async def travel_back_date_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for travel date.
        This will use the DATE_RESOLVER_DIALOG."""

        booking_details = step_context.options

        # Capture the results of the previous step
        booking_details.travel_date = step_context.result
        if not booking_details.travel_back_date or self.is_ambiguous(
            booking_details.travel_back_date
        ):
            return await step_context.begin_dialog(
                "returnDateDialogue", booking_details.travel_back_date
            )  # pylint: disable=line-too-long

        return await step_context.next(booking_details.travel_back_date)

    async def confirm_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Confirm the information the user has provided."""
        booking_details = step_context.options

        # Capture the results of the previous step
        booking_details.travel_back_date = step_context.result

        # Warn the user if the travel date is after the return date.
        if booking_details.travel_date > booking_details.travel_back_date:
            await step_context.context.send_activity(
                "Be careful! The return date is before the travel date."
            )

        msg = (
            f"Please confirm, I have you traveling to: { booking_details.destination }"
            f" from: { booking_details.origin } on: { booking_details.travel_date} and return for { booking_details.travel_back_date}  for {booking_details.max_budget} dollars maximum.."
        )

        # Offer a YES/NO prompt.
        return await step_context.prompt(
            ConfirmPrompt.__name__, PromptOptions(prompt=MessageFactory.text(msg))
        )

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Complete the interaction and end the dialog."""
        if step_context.result:
            booking_details = step_context.options
            # booking_details.travel_back_date = step_context.result

            properties = {}
            properties["DialogId"] = self.dialog_id
            self.telemetry_client.track_event("SuggestionConfirmed", properties)
            print("CustomEvent : SuggestionConfirmed")

            return await step_context.end_dialog(booking_details)

        properties = {}
        properties["DialogId"] = self.dialog_id
        self.telemetry_client.track_event("SuggestionRefuting", properties)
        print("CustomEvent : SuggestionRefuting")

        return await step_context.end_dialog()

    def is_ambiguous(self, timex: str) -> bool:
        """Ensure time is correct."""
        timex_property = Timex(timex)
        return "definite" not in timex_property.types
