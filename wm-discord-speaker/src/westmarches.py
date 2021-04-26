import json
import os
import pickle
import random
import re
from typing import List

import discord
import numpy
import spacy
import tflearn
import tensorflow as tf
from redbot.core import commands, Config
from redbot.core.bot import Red  # Only used for type hints
from redbot.core.utils.chat_formatting import pagify
from spacy.lang.fr.stop_words import STOP_WORDS
from spacy.tokens.token import Token

PUNCTUATION = list("?:!.,;")


class WestMarchesCog(commands.Cog):
    default_guild_settings = {
        "rumors": []
    }

    def __init__(self, bot: Red):
        super().__init__()

        self._labels = None
        self._network = None
        self._model = None
        self._known_words = None
        self.bot = bot
        self.data_path = os.path.dirname(__file__) + '/data/model'
        self.nlp = spacy.load('fr_core_news_sm')

        self.config = Config.get_conf(self, identifier=567346224)
        self.config.register_global(**self.default_guild_settings)
        self.config.register_guild(**self.default_guild_settings)

        STOP_WORDS.add('bot_self')

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

    def _predict(self, message):
        words = self._tokenize(message)
        bag = [(1 if word in words else 0) for word in self._get_known_words()]

        result = self._get_model().predict([numpy.array(bag)])[0]

        return self._get_labels()[numpy.argmax(result)]

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        ctx = await self.bot.get_context(message)  # type: commands.Context

        if str(self.bot.user.id) in message.content:
            clean_message = re.sub('<@!?([0-9]*)>', 'bot_self', message.content)
            print(clean_message)
            intent = self._predict(clean_message)

            await ctx.send(intent)

    @commands.group(invoke_without_command=True)
    async def rumors(self, ctx: commands.Context):
        await ctx.send(random.choice(await self.config.guild(ctx.guild).rumors()))

    @rumors.command("add")
    async def add_rumor(self, ctx: commands.Context, *new_rumor):
        async with self.config.guild(ctx.guild).rumors() as rumors:
            rumors.append(" ".join(new_rumor))
        await ctx.send("Nouvelle rumeur enregistrée.")

    @rumors.command("ls")
    async def list_rumors(self, ctx: commands.Context):
        async with self.config.guild(ctx.guild).rumors() as rumors:
            indexed_rumors = []
            for i, rumor in enumerate(rumors):
                indexed_rumors.append('{} - {}'.format(i, rumor))
            for page in pagify(", ".join(indexed_rumors), delims=[", ", "\n"], page_length=120):
                await ctx.send(page)

    @rumors.command("rm")
    async def del_rumor(self, ctx: commands.Context, rumor_id: int):
        old_rumor = None

        async with self.config.guild(ctx.guild).rumors() as rumors:
            old_rumor = rumors[rumor_id]
            del rumors[rumor_id]
            self.config.guild(ctx.guild).rumors.set(rumors)

        await ctx.send("Rumeur supprimée : {}".format(old_rumor))

    @commands.command()
    async def train(self, ctx: commands.Context):
        await ctx.send('Training started...')
        self._train(self._load_intents())
        await ctx.send('Training completed.')

    def _tokenize(self, message) -> List[Token]:
        return [token.lemma_.lower() for token in self.nlp(message) if
                len(token.text.strip()) > 0
                and token.text.strip().lower() not in STOP_WORDS
                and token.text.strip() not in PUNCTUATION]

    def _get_filename(self, filename: str):
        return "{}/{}".format(self.data_path, filename)

    def _get_network(self, force_new=False):
        if self._network is None or force_new is True:
            training = self._load_data('input.pickle')
            output = self._load_data('output.pickle')

            self._network = self._create_network(training, output)
        return self._network

    def _create_network(self, training, output):
        net = tflearn.input_data(shape=[None, len(training[0])])
        net = tflearn.fully_connected(net, 8)
        net = tflearn.fully_connected(net, 8)
        net = tflearn.fully_connected(net, len(output[0]), activation="softmax")
        return tflearn.regression(net)

    def _get_model(self):
        filename = self._get_filename('model.tflearn')

        if self._model is None:
            if os.path.isfile(filename + '.index'):
                model = tflearn.DNN(self._get_network())
                model.load(filename, weights_only=True)
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

    def _save_model(self, model, filename):
        model.save(self._get_filename(filename))

    def _save_data(self, data, filename):
        with open(self._get_filename(filename), "wb") as f:
            pickle.dump(data, f)

    def _load_data(self, filename: str):
        with open(self._get_filename(filename), "rb") as f:
            return pickle.load(f)

    def _load_intents(self):
        with open(self._get_filename('intents.json')) as file:
            return json.load(file)
