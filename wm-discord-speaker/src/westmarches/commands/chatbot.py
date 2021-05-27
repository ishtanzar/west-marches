import json
import logging
import pickle
import re
from typing import Mapping, List

import discord
import numpy
import spacy
import tensorflow as tf
import tflearn
from redbot.core import commands, data_manager
from spacy.lang.fr.stop_words import STOP_WORDS
from spacy.tokens.token import Token
from tflearn import DNN

from westmarches import MixinMeta
from westmarches.utils import CompositeMetaClass

PUNCTUATION = list("?:!.,;")
log = logging.getLogger("westmarches.cogs.chatbot")


class ChatbotCommands(MixinMeta, metaclass=CompositeMetaClass):

    def __init__(self) -> None:
        super().__init__()

        self._labels = None
        self._network = None
        self._model = None
        self._known_words = None
        self.nlp = spacy.load('fr_core_news_sm')

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        ctx = await self.bot.get_context(message)  # type: commands.Context

        if str(self.bot.user.id) in message.content:
            clean_message = re.sub('<@!?([0-9]*)>', '', message.content)
            intent = self._predict(clean_message)

            if intent == "rumors":
                await self.bot.all_commands.get("rumors").invoke(ctx)
            else:
                await ctx.send(intent)

    @commands.command()
    async def learn(self, ctx: commands.Context, new_intent):
        if ctx.message.reference:
            message = await ctx.fetch_message(ctx.message.reference.message_id)
            clean_message = re.sub('<@!?([0-9]*)>', '', message.content).strip()
            json = self._load_intents()
            create_intent = True

            for intent in json["intents"]:
                if new_intent == intent["tag"]:
                    intent["patterns"].append(clean_message)
                    create_intent = False

            if create_intent:
                json["intents"].append({
                    "tag": new_intent,
                    "patterns": [clean_message]
                })

            self._save_intents(json)

    @commands.command()
    async def train(self, ctx: commands.Context):
        await ctx.send('Training started...')
        self._train(await self._load_intents())
        await ctx.send('Training completed.')

    async def _load_intents(self) -> Mapping:
        intents = await self.config.intents()
        if not intents:
            log.info('No saved invents, loading defaults')
            with (data_manager.cog_data_path(self) / 'intents.json').open('r') as file:
                intents = json.load(file)
        return intents

    def _save_intents(self, intents):
        self.config.intents.set(intents)

    def _train(self, data):
        all_words = []
        labels = []
        docs_x = []
        docs_y = []

        for intent in data["intents"]:
            for pattern in intent["patterns"]:
                words = self._tokenize(pattern)
                all_words.extend(words)
                docs_x.append(words)
                docs_y.append(intent["tag"])

            if intent["tag"] not in labels:
                labels.append(intent["tag"])

        all_words = sorted(list(set(all_words)))
        labels = sorted(labels)

        training = []
        output = []
        out_empty = [0 for _ in range(len(labels))]
        for x, doc in enumerate(docs_x):
            bag = [(1 if word in doc else 0) for word in all_words]

            output_row = out_empty[:]
            output_row[labels.index(docs_y[x])] = 1

            training.append(bag)
            output.append(output_row)

        training = numpy.array(training)
        output = numpy.array(output)

        with tf.compat.v1.Graph().as_default():
            network = self._create_network(training, output)
            model = tflearn.DNN(network)

            model.fit(training, output, n_epoch=1000, batch_size=8, show_metric=True)

        self._save_data(labels, 'labels.pickle')
        self._save_data(all_words, 'known_words.pickle')
        self._save_data(training, 'input.pickle')
        self._save_data(output, 'output.pickle')

        self._save_model(model, 'model.tflearn')

        self._labels = labels
        self._known_words = all_words
        self._network = network
        self._model = model
        # tf.compat.v1.reset_default_graph()
        # tf.compat.v1.Graph().as_default()

    def _tokenize(self, message) -> List[Token]:
        return [token.lemma_.lower() for token in self.nlp(message) if
                len(token.text.strip()) > 0
                and token.text.strip().lower() not in STOP_WORDS
                and token.text.strip() not in PUNCTUATION]

    def _create_network(self, training, output):
        net = tflearn.input_data(shape=[None, len(training[0])])
        net = tflearn.fully_connected(net, 8)
        net = tflearn.fully_connected(net, 8)
        net = tflearn.fully_connected(net, len(output[0]), activation="softmax")
        return tflearn.regression(net)

    def _predict(self, message):
        words = self._tokenize(message)
        bag = [(1 if word in words else 0) for word in self._get_known_words()]

        result = self._get_model().predict([numpy.array(bag)])[0]

        return self._get_labels()[numpy.argmax(result)]

    def _save_model(self, model: DNN, filename):
        model.save(str(data_manager.cog_data_path(self) / filename))

    def _save_data(self, data, filename):
        with (data_manager.cog_data_path(self) / filename).open('wb') as f:
            pickle.dump(data, f)

    def _get_model(self):
        filename = (data_manager.cog_data_path(self) / 'model.tflearn')

        if self._model is None and filename.with_name('model.tflearn.index').is_file():
            model = tflearn.DNN(self._get_network())
            model.load(str(filename), weights_only=True)
            self._model = model

        return self._model

    def _get_known_words(self):
        if self._known_words is None:
            self._known_words = self._load_data('known_words.pickle')

        return self._known_words

    def _get_labels(self):
        if self._labels is None:
            self._labels = self._load_data('labels.pickle')

        return self._labels

    def _load_data(self, filename: str):
        with (data_manager.cog_data_path(self) / filename).open('rb') as f:
            return pickle.load(f)

    def _get_network(self, force_new=False):
        if self._network is None or force_new is True:
            training = self._load_data('input.pickle')
            output = self._load_data('output.pickle')

            self._network = self._create_network(training, output)
        return self._network
