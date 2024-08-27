# -*- coding: utf-8 -*-
"""book_final

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1l6IhNiVIxcPe4ZMbGiR5qZgSjNv9vEbb
"""

# Commented out IPython magic to ensure Python compatibility.
# Import libraries
# %pip install pyspellchecker

from spellchecker import SpellChecker
import tensorflow as tf
from tensorflow.keras.layers.experimental import preprocessing
import numpy as np
import os
import time

# Load file data
#path_to_file = tf.keras.utils.get_file('austen.txt', 'https://raw.githubusercontent.com/byui-cse/cse450-course/master/data/austen/austen.txt')
text = open('/content/Edgar_Allen_Poe.txt', 'rb').read().decode(encoding='utf-8')
print('Length of text: {} characters'.format(len(text)))
print(text[:200])

# Get the list of unique characters in the file
vocab = sorted(set(text))
print('{} unique characters'.format(len(vocab)))
print(vocab)

# Encode these characters into numbers
ids_from_chars = preprocessing.StringLookup(vocabulary=list(vocab))
chars_from_ids = tf.keras.layers.experimental.preprocessing.StringLookup(vocabulary=ids_from_chars.get_vocabulary(), invert=True)

# Helper function to turn a sequence of ids back into a string
def text_from_ids(ids):
    joinedTensor = tf.strings.reduce_join(chars_from_ids(ids), axis=-1)
    return joinedTensor.numpy().decode("utf-8")

# Verify that they work
testids = ids_from_chars(["T", "r", "u", "t", "h"])
print(chars_from_ids(testids))
testString = text_from_ids(testids)
print(testString)

# Create a stream of encoded integers from the text
all_ids = ids_from_chars(tf.strings.unicode_split(text, 'UTF-8'))
all_ids

# Convert that into a tensorflow dataset
ids_dataset = tf.data.Dataset.from_tensor_slices(all_ids)

# Batch these sequences up into chunks for training
seq_length = 100
sequences = ids_dataset.batch(seq_length+1, drop_remainder=True)

# Function to generate sequence pairs
def split_input_target(sequence):
    input_text = sequence[:-1]
    target_text = sequence[1:]
    return input_text, target_text

# Create a new dataset of input->target pairs
dataset = sequences.map(split_input_target)

# Verify the sequences
for input_example, target_example in dataset.take(1):
    print("Input: ", text_from_ids(input_example))
    print("--------")
    print("Target: ", text_from_ids(target_example))

# Randomize the sequences and build a streaming dataset
BATCH_SIZE = 64
BUFFER_SIZE = 10000

dataset = (
    dataset
    .shuffle(BUFFER_SIZE)
    .batch(BATCH_SIZE, drop_remainder=True)
    .prefetch(tf.data.experimental.AUTOTUNE)
)

class EnhancedTextModel(tf.keras.Model):
    def __init__(self, vocab_size, embedding_dim, rnn_units):
        super().__init__()
        self.embedding = tf.keras.layers.Embedding(vocab_size, embedding_dim)
        self.lstm1 = tf.keras.layers.LSTM(rnn_units, return_sequences=True, return_state=True)
        self.gru = tf.keras.layers.GRU(rnn_units, return_sequences=True, return_state=True)
        self.lstm2 = tf.keras.layers.LSTM(rnn_units, return_sequences=True, return_state=True)
        self.dense = tf.keras.layers.Dense(vocab_size)

    def call(self, inputs, states=None, return_state=False, training=False):
        x = self.embedding(inputs, training=training)

        # Initialize states if they are None
        if states is None:
            states_lstm1 = self.lstm1.get_initial_state(x)
            states_gru = self.gru.get_initial_state(x)
            states_lstm2 = self.lstm2.get_initial_state(x)
        else:
            states_lstm1, states_gru, states_lstm2 = states

        x, state_lstm1_h, state_lstm1_c = self.lstm1(x, initial_state=states_lstm1, training=training)
        x, state_gru = self.gru(x, initial_state=states_gru, training=training)
        x, state_lstm2_h, state_lstm2_c = self.lstm2(x, initial_state=states_lstm2, training=training)
        x = self.dense(x, training=training)

        if return_state:
            return x, [[state_lstm1_h, state_lstm1_c], state_gru, [state_lstm2_h, state_lstm2_c]]
        else:
            return x

# Instantiate the model
vocab_size = len(ids_from_chars.get_vocabulary())
embedding_dim = 256
rnn_units = 1024

model = EnhancedTextModel(vocab_size, embedding_dim, rnn_units)

# Verify the output of the model
for input_example_batch, target_example_batch in dataset.take(1):
    example_batch_predictions, _ = model(input_example_batch, states=None, return_state=True)
    print(example_batch_predictions.shape, "# (batch_size, sequence_length, vocab_size)")

# View the model summary
model.summary()

# Compile the model
loss = tf.losses.SparseCategoricalCrossentropy(from_logits=True)
model.compile(optimizer='adam', loss=loss)

# Fit the model
history = model.fit(dataset, epochs=20)

class OneStep(tf.keras.Model):
    def __init__(self, model, chars_from_ids, ids_from_chars, temperature=1.0):
        super().__init__()
        self.temperature = temperature
        self.model = model
        self.chars_from_ids = chars_from_ids
        self.ids_from_chars = ids_from_chars
        skip_ids = self.ids_from_chars(['', '[UNK]'])[:, None]
        sparse_mask = tf.SparseTensor(
            values=[-float('inf')] * len(skip_ids),
            indices=skip_ids,
            dense_shape=[len(ids_from_chars.get_vocabulary())]
        )
        self.prediction_mask = tf.sparse.to_dense(sparse_mask, validate_indices=False)

    @tf.function
    def generate_one_step(self, inputs, states=None):
        input_chars = tf.strings.unicode_split(inputs, 'UTF-8')
        input_ids = self.ids_from_chars(input_chars).to_tensor()
        predicted_logits, states = self.model(inputs=input_ids, states=states, return_state=True)
        predicted_logits = predicted_logits[:, -1, :]
        predicted_logits = predicted_logits / self.temperature
        predicted_logits = predicted_logits + self.prediction_mask
        predicted_ids = tf.random.categorical(predicted_logits, num_samples=1)
        predicted_ids = tf.squeeze(predicted_ids, axis=-1)
        return self.chars_from_ids(predicted_ids), states

# Create an instance of the character generator
one_step_model = OneStep(model, chars_from_ids, ids_from_chars)

# Generate a 1000 character chapter
states = None
next_char = tf.constant(['The world seemed like such a peaceful place until the magic tree was discovered in London.'])
result = [next_char]

for n in range(1000):
    next_char, states = one_step_model.generate_one_step(next_char, states=states)
    result.append(next_char)

result = tf.strings.join(result)

# Print the results formatted
generated_text = result[0].numpy().decode('utf-8')
print(generated_text)

# Spell checking
import string
spell = SpellChecker()
words = generated_text.split()
punctuation_and_quotes = string.punctuation + '“”‘’'
table = str.maketrans('', '', punctuation_and_quotes)
words = [word.translate(table) for word in words]
misspelled = spell.unknown(words)
print(misspelled)
print(len(words) / len(misspelled))

import matplotlib.pyplot as plt
import seaborn as sns

# Ejemplo de curva de pérdida durante el entrenamiento
epochs = range(1, 21)  # Ejemplo de 20 épocas
loss = [0.6, 0.5, 0.45, 0.4, 0.35, 0.3, 0.28, 0.26, 0.24, 0.22, 0.2, 0.19, 0.18, 0.17, 0.16, 0.15, 0.14, 0.13, 0.12, 0.11]

plt.figure(figsize=(10, 6))
plt.plot(epochs, loss, label='Training Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.title('Training Loss Curve')
plt.legend()
plt.show()

# Ejemplo de histograma de longitud de secuencias generadas
generated_text_lengths = [len(text) for text in generated_texts]  # 'generated_texts' es una lista de textos generados

plt.figure(figsize=(10, 6))
sns.histplot(generated_text_lengths, bins=20)
plt.xlabel('Length of Generated Text')
plt.ylabel('Frequency')
plt.title('Distribution of Generated Text Lengths')
plt.show()

# Ejemplo de distribución de palabras en el texto generado (word cloud)
from wordcloud import WordCloud

wordcloud = WordCloud(width=800, height=400, background_color='white').generate(' '.join(generated_texts))

plt.figure(figsize=(10, 6))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.title('Word Cloud of Generated Texts')
plt.show()

import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from wordcloud import WordCloud

# Texto original de Jane Austen
original_text = text  # 'text' contiene las obras originales de Jane Austen
original_words = original_text.split()
original_char_count = Counter(original_text)
original_word_count = Counter(original_words)

# Texto generado por el modelo
generated_text = generated_text  # 'generated_text' es el texto generado por el modelo
generated_words = generated_text.split()
generated_char_count = Counter(generated_text)
generated_word_count = Counter(generated_words)

# Top 20 palabras más comunes en el texto original y generado
top_original_words = dict(original_word_count.most_common(20))
top_generated_words = dict(generated_word_count.most_common(20))

# Histograma de distribución de palabras
plt.figure(figsize=(14, 7))

plt.subplot(1, 2, 1)
sns.barplot(x=list(top_original_words.values()), y=list(top_original_words.keys()), palette="viridis")
plt.title('Top 20 Words in Jane Austen\'s Original Text')
plt.xlabel('Frequency')
plt.ylabel('Words')

plt.subplot(1, 2, 2)
sns.barplot(x=list(top_generated_words.values()), y=list(top_generated_words.keys()), palette="viridis")
plt.title('Top 20 Words in Generated Text')
plt.xlabel('Frequency')
plt.ylabel('Words')

plt.tight_layout()
plt.show()

# Word Cloud de texto original
original_wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(original_word_count)
plt.figure(figsize=(10, 6))
plt.imshow(original_wordcloud, interpolation='bilinear')
plt.axis('off')
plt.title('Word Cloud of Jane Austen\'s Original Text')
plt.show()

# Word Cloud de texto generado
generated_wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(generated_word_count)
plt.figure(figsize=(10, 6))
plt.imshow(generated_wordcloud, interpolation='bilinear')
plt.axis('off')
plt.title('Word Cloud of Generated Text')
plt.show()