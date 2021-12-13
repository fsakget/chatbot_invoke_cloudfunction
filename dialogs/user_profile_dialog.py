# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.dialogs import (
    ComponentDialog,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from botbuilder.dialogs.prompts import (
    TextPrompt,
    ChoicePrompt,
    PromptOptions,
)
from botbuilder.dialogs.choices import Choice
from botbuilder.core import MessageFactory, UserState

from data_models import UserProfile

import requests


class UserProfileDialog(ComponentDialog):
    def __init__(self, user_state: UserState):
        super(UserProfileDialog, self).__init__(UserProfileDialog.__name__)

        self.user_profile_accessor = user_state.create_property("UserProfile")

        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.option_step,
                    self.get_information_step,
                    self.summary_step,
                ],
            )
        )
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(ChoicePrompt(ChoicePrompt.__name__))

        self.initial_dialog_id = WaterfallDialog.__name__

    async def option_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        # WaterfallStep always finishes with the end of the Waterfall or with another dialog;
        # here it is a Prompt Dialog. Running a prompt here means the next WaterfallStep will
        # be run when the users response is received.
        return await step_context.prompt(
            ChoicePrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text( """\nOlá! Bem vindo ao chatbot disponibilizador de imagens para Docker Desktop.
                                               \nSelecione uma das opções abaixo:
                                            """),
                choices=[Choice("Scanear Imagem"), Choice("Status Scan"), Choice("Resultado Scan")],
            ),
        )

    async def get_information_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["options"] = step_context.result.value
        op = step_context.result.value

        if op == "Scanear Imagem":
            return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(f"""Informe a imagem + tag. 
                                                                                                            \nEx: grafana/grafana:latest ou ubuntu:v3 """
                                                                                                            )),)
        elif op == "Status Scan":
            return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(f"Informe o ID do Scan.")),)
        else:
            return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(f"Informe o ID do Scan para ver os logs da análise.")),)

    async def summary_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:

        step_context.values["params"] = step_context.result
    
        if step_context.result:
            # Get the current profile object from user state.  Changes to it
            # will saved during Bot.on_turn.
            user_profile = await self.user_profile_accessor.get(
                step_context.context, UserProfile
            )

            user_profile.params = step_context.values["params"]
            user_profile.options = step_context.values["options"]

            #msg = f"I have your opcao {user_profile.options} and your params eh {user_profile.params}."

            if user_profile.options == "Scanear Imagem":
                op = "start_scan"
            elif user_profile.options == "Status Scan":
                op = "get_status"
            else:
                op = "get_result_scan"

            payload = {'operacao': op, 'cloudbuild_execution_id': user_profile.params, 'imagem': user_profile.params, 'registry': '' }
            
            endpoint = "xxxxxxxxxx"

            #req = urllib.request.Request(endpoint)
            #auth_req = google.auth.transport.requests.Request()
            #id_token = google.oauth2.id_token.fetch_id_token(auth_req, endpoint)
            #req.add_header("Authorization", f"Bearer {id_token}")
            #response = urllib.request.post(endpoint, json = payload)

            response = requests.post(endpoint, json = payload)

            if response.status_code == 200:
                #print(dir(response))
                await step_context.context.send_activity(f"{ response.text }")
            else:
                await step_context.context.send_activity(f"""\nError: \"{ response.status_code }\" 
                                                            \nVerifique se o ID informado é válido!
                                                            """)
        else:
            await step_context.context.send_activity(
                MessageFactory.text("Thanks! Bye-bye.")
            )

        # WaterfallStep always finishes with the end of the Waterfall or with another
        # dialog, here it is the end.
        return await step_context.end_dialog()
