import sys
from random import randrange
from collections import deque
from keras.models import Sequential
from keras.layers import Conv2D, Dense, Flatten
from keras.optimizers import Adam
import numpy as np
from ale_python_interface import ALEInterface

if len(sys.argv) < 2:
    print('Usage:', sys.argv[0], 'rom_file.bin')
    sys.exit()

ale = ALEInterface()
ale.setInt(b'random_seed', 123)
ale.setBool(b'display_screen', True)
rom_file = str.encode(sys.argv[1])
ale.loadROM(rom_file)


class DeepQ():
    def __init__(self):
        # Parameters
        self.minibatch_size = 64
        self.num_stacked_frames = 3
        self.epsilon = 0.1  # Exploration rate
        self.epsilon_floor = 0.05
        self.epsilon_decay_rate = 0.99
        self.gamma = 0.95  # Discount rate
        self.learning_rate = 0.00001

        self.valid_action_set = ale.getMinimalActionSet()
        self.model = self.build_q_network()
        self.experience_memory = deque(maxlen=2000)

    def build_q_network(self):
        '''
        Builds the CNN (from https://github.com/yilundu/DQN-DDQN-on-Space-Invaders/blob/master/deep_Q.py),
        that takes preprocessed frames as input and outputs
        Q-Values for each available action in the game.

        Frames have been cropped to 84x84 pixels and converted to greyscale for
        computational efficiency as color does not effect gameplay
        '''

        model = Sequential()
        model.add(Conv2D(
            32,
            (8, 8),
            input_shape=(84, 84, self.num_stacked_frames),
            strides=(4, 4),
            activation='relu'
        ))
        model.add(Conv2D(64, (4, 4), strides=(2, 2), activation='relu'))
        model.add(Conv2D(64, (3, 3), activation='relu'))
        model.add(Flatten())
        model.add(Dense(512, activation='relu'))
        model.add(Dense(len(self.valid_action_set), activation='linear'))
        model.compile(loss='mse', optimizer=Adam(lr=self.learning_rate))
        return model

    def predict_move(self, state):
        q_values = self.model.predict(
            state.reshape(1, 84, 84, self.num_stacked_frames),
            batch_size=1
        )

        optimal_policy = np.argmax(q_values)  # Index of the best Q Value
        if np.random.random() < self.epsilon:
            optimal_policy = np.random.choice(self.valid_action_set)

        # Translate the index of the highest Q value action to an action
        # in the games set. This is required as the games action set may look
        # like this: [0, 1, 2, 3, 6, 17, 18]
        optimal_action = self.valid_action_set[optimal_policy]

        return optimal_action, q_values[0, optimal_policy]


try:
    for episode in range(10):
        total_reward = 0
        while not ale.game_over():
            a = specific_actions[randrange(len(specific_actions))]
            reward = ale.act(a)
            total_reward += reward

        print('Episode ended with score:', total_reward)
        ale.reset_game()

except KeyboardInterrupt:
    print('Shutting Down')
