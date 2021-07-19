import json
import logging
from asyncio import Future
from enum import Enum
from pathlib import Path
from typing import Optional

# from tflearn import DNN
from montydb import MontyCursor

from services.database import Engine
from utils import get_logger

PUNCTUATION = list("?:!.,;")


class ModelCollection(str, Enum):
    LABELS = 'labels',
    KNOWN_WORDS = 'known_words',
    INPUT = 'input',
    OUTPUT = 'output'


class IntentService:
    # _model: DNN

    # noinspection PyUnresolvedReferences
    _nlp: "Language"
    _database: Engine
    _setup_task: Optional[Future] = None

    _ready = False
    _intents_col_prefix = 'ai.intents.intent.'
    _models_col_prefix = 'ai.intents.model.'

    def __init__(self, database: Engine, model_dir: Path) -> None:
        super().__init__()

        self.log = get_logger(self)
        self._database = database
        self._model_dir = model_dir

    def setup(self, task: Optional[Future] = None):
        self.log.debug('Setup, task=' + str(task))
        self._setup_task = task

        # noinspection PyPackageRequirements
        import spacy

        self._nlp = spacy.load('fr_core_news_sm')
        self.log.debug('Setup completed')
        self._ready = True

    def list_patterns(self, intent):
        return self.scan_dictionary(self._intents_col_prefix + intent)

    def add_pattern(self, intent, param):
        self._database.collection(self._intents_col_prefix + intent).insert_one({'value': param})

    def train(self):
        import tensorflow
        import tflearn
        import numpy

        from tensorflow.python.compat.v2_compat import disable_v2_behavior

        all_words = []
        labels = []
        docs_x = []
        docs_y = []

        self.log.debug('Reading intents')
        for intent in self.intents:
            for pattern in self.scan_dictionary(self._intents_col_prefix + intent):
                words = self.tokenize(pattern)
                all_words.extend(words)
                docs_x.append(words)
                docs_y.append(intent)

            if intent not in labels:
                labels.append(intent)

        all_words = sorted(list(set(all_words)))
        labels = sorted(labels)

        training = []
        output = []
        out_empty = [0 for _ in range(len(labels))]

        self.log.debug('Preparing output containers')
        for x, doc in enumerate(docs_x):
            bag = [(1 if word in doc else 0) for word in all_words]

            output_row = out_empty[:]
            output_row[labels.index(docs_y[x])] = 1

            training.append(bag)
            output.append(output_row)

        with tensorflow.compat.v1.Graph().as_default():
            numpy_in = numpy.array(training)
            numpy_out = numpy.array(output)

            network = self.network(numpy_in, numpy_out)

            self.log.debug('Creating model')
            model = tflearn.DNN(network)

            self.log.debug('Training model')
            disable_v2_behavior()
            model.fit(numpy_in, numpy_out, n_epoch=1000, batch_size=8)

        self.log.debug('Saving')
        self.purge_model()

        self._database.create_collection(self._models_col_prefix + ModelCollection.LABELS,
                                         [{'value': p} for p in labels])
        self._database.create_collection(self._models_col_prefix + ModelCollection.KNOWN_WORDS,
                                         [{'value': p} for p in all_words])
        self._database.create_collection(self._models_col_prefix + ModelCollection.INPUT,
                                         [{'value': p} for p in training])
        self._database.create_collection(self._models_col_prefix + ModelCollection.OUTPUT,
                                         [{'value': p} for p in output])
        model.save(self.model_filename)

    def predict(self, message: str):
        import numpy
        import tensorflow

        words = self.tokenize(message)
        bag = [(1 if word in words else 0) for word in self.known_words]

        with tensorflow.compat.v1.Graph().as_default():
            result = self.model.predict([numpy.array(bag)])[0]

        return self.labels[numpy.argmax(result)]

    # noinspection PyUnresolvedReferences
    def tokenize(self, message) -> ["Token"]:
        # noinspection PyPackageRequirements
        from spacy.lang.fr.stop_words import STOP_WORDS

        return [token.lemma_.lower() for token in self.nlp(message) if
                len(token.text.strip()) > 0
                and token.text.strip().lower() not in STOP_WORDS
                and token.text.strip() not in PUNCTUATION]

    def purge_model(self):
        for collection in ['labels', 'known_words', 'input', 'output']:
            self._database.drop_collection(self._models_col_prefix + collection)

    def purge_intents(self):
        for intent in self.intents:
            self._database.drop_collection(self._intents_col_prefix + intent)

    def import_intents(self, file_path: Path):
        with file_path.open('r') as file:
            json_intents = json.load(file)

        self.purge_intents()

        for intent in json_intents['intents']:
            if intent['patterns']:
                self._database.create_collection(self._intents_col_prefix + intent['tag'],
                                                 [{'value': p} for p in intent['patterns']])

    def backup_intents(self, file_path: Path):
        intents = []
        for intent in self.intents:
            intents.append({
                'tag': intent,
                'patterns': self.scan_dictionary(self._intents_col_prefix + intent)
            })

        with file_path.open('w') as file:
            json.dump({'intents': intents}, file)

    def scan_dictionary(self, collection_name: str):
        return [i['value'] for i in self._database.scan(collection_name)]

    def network(self, training, output):
        self.log.debug('Creating network')
        import tflearn

        net = tflearn.input_data(shape=[None, len(training[0])])
        net = tflearn.fully_connected(net, 8)
        net = tflearn.fully_connected(net, 8)
        net = tflearn.fully_connected(net, len(output[0]), activation="softmax")
        return tflearn.regression(net)

    @property
    async def ready(self):
        if (not self._ready) and self._setup_task:
            await self._setup_task
            return self._setup_task.done() and self._ready
        return self._ready

    # noinspection PyUnresolvedReferences
    @property
    def nlp(self) -> "Language":
        if not self._nlp:
            self.setup()
        return self._nlp

    @property
    def model_filename(self):
        return str(self._model_dir / 'model.tflearn')

    @property
    def intents(self) -> [str]:
        return [c.split('.')[-1] for c in self._database.collections() if c.startswith(self._intents_col_prefix)]

    @property
    def known_words(self) -> [str]:
        return self.scan_dictionary(self._models_col_prefix + ModelCollection.KNOWN_WORDS)

    @property
    def labels(self) -> [str]:
        return self.scan_dictionary(self._models_col_prefix + ModelCollection.LABELS)

    @property
    def input(self) -> [str]:
        return self.scan_dictionary(self._models_col_prefix + ModelCollection.INPUT)

    @property
    def output(self) -> [str]:
        return self.scan_dictionary(self._models_col_prefix + ModelCollection.OUTPUT)

    @property
    def model(self):
        self.log.debug('Loading model')
        import tflearn

        model = tflearn.DNN(self.network(self.input, self.output))
        model.load(self.model_filename, weights_only=True)

        return model
