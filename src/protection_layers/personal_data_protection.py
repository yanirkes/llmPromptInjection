import gensim.downloader
import nltk
import spacy
nltk.download('stopwords')
nltk.download('punkt')
from nltk.corpus import stopwords
import pandas as pd
import re
import logging
import time

# Show all available models in gensim-data
stop_words = set(stopwords.words('english'))

# how to remove a word in a set?
for word in ['am', 'she', 'he', 'it', 'they', 'you', 'me', 'my', 'myself', 'our', 'ours']:
    stop_words.remove(word)


class PersonalDataProtector():

    def __init__(self, prompt, glove_vectors):
        self.glove_vectors = glove_vectors
        self.user_personal_state_words = []
        self.prompt = self.set_prompt(prompt)
        self.msg_dict = {}
        self.n2_seq_df = pd.DataFrame()
        self.subjects = ['disease', 'medical', 'sickness', 'physical']
        self.to_prompt = ''

    @staticmethod
    def is_date(word):
        """Check if the text matches a date format """
        pattern = r"^\d{4}-\d{2}-\d{2}$|^(\d{1,2})/(\d{1,2})/\d{4}$|^(\d{1,2}).(\d{1,2}).\d{4}$|^(\d{4}).(\d{1,2}).\d{2}$"
        match = re.search(pattern, word)

        return bool(match)

    @staticmethod
    def is_currency(word):
        """Check if the text matches a currency pattern"""
        pattern = r"[$€¥\£\₩]"
        match = re.search(pattern, word)

        return bool(match)

    @staticmethod
    def is_id(word):
        """Find id patterns - the id could be contains both letters and numbers"""
        try:
            if isinstance(word, int(word)):
                if len(word) > 7:
                    return True
                else:
                    return False
        except:
            pattern = r"[^\d\-+\.]"
            processed_word = re.sub(pattern, "", word)
            if len(processed_word) > 5:
                return True
            else:
                return False

    @staticmethod
    def simple_preprocess(text):
        """Apply some basics text pre-process"""
        # Replace non-alphanumeric characters (excluding numerical figures) with spaces
        pattern = r"[^\w\d\s]+"
        filtered_text = re.sub(pattern, ' ', text)

        # Remove extra spaces
        filtered_text = re.sub(r' +', ' ', filtered_text)

        # Remove extra linespaces
        filtered_text = re.sub(r'\n', ' ', filtered_text)

        # Remove stopwords
        tokens = [word for word in filtered_text.split(' ') if word not in stop_words]

        # Return the list of tokens
        return tokens

    @staticmethod
    def calc_similarity(glove_vectors, word_a, word_b):
        """If word b exist in the model corpus then calc similarity between the two words, else return 0"""
        try:
            return glove_vectors.similarity(word_a, word_b)
        except:
            return 0

    @staticmethod
    def is_day_of_the_week(word):
        """Check if the text contain any information on the day of the week"""
        pattern = r"^monday|^tuesday|^wednesday|^thursday|^friday|^saturday|^sunday$"
        match = re.search(pattern, str.lower(word))
        return match

    def set_prompt(self, prompt):
       return re.sub(r'\n', ' ', prompt)


    def block_basic_personal_data(self, word):
        """On every word, it runs validations to verify if the word has a user personal data characteristic"""
        if self.is_date(word):
            return '#####'
        elif self.is_currency(word):
            return '#####'
        elif self.is_id(word):
            return '#####'
        elif self.is_day_of_the_week(word):
            return '#####'
        else:
            return word

    def create_sequential_df(self):
        """Convert the text into a two-step sequential dataset, where each row comprises one
         word from the text alongside the following two words.

         Notice: the first column of the resulted dataframe are only personal pronoun to detect
         when the expose a personal info on himself or is relatives
         """
        # Simple process the text
        filtered_text = self.simple_preprocess(self.prompt)

        # zip word t+1 with word t+2
        next_two_words_tuples = [(word_a, word_b) for word_a, word_b in zip(filtered_text[1:-1], filtered_text[2::])]

        # zip word t with the tuple (t+1,t+2)
        temp = [(word_a, word_b[0], word_b[1]) for word_a, word_b in zip(filtered_text[0:-2], next_two_words_tuples)]

        # Convert to dataframe
        df = pd.DataFrame(temp, columns=['word_a', 'word_b', 'word_c'])


        personal_pronoun = [
            'I', 'name', 'am', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself',
            'yourselves', 'he', 'him', 'his', 'himself','she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they',
            'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',
            'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
            'did'
        ]

        # Filter non personal pronouns
        mask = df['word_a'].isin(personal_pronoun)
        self.n2_seq_df = df[mask]

    def compute_similarity_for_column(self, subject, confidence):
        """Measuring similarity between a specific subject and a word from a sequential dataframe.
           This comparison is done for each row. After assessing all rows, we identify similarities
           that exceed a predetermined confidence threshold. Subsequently, the rows are converted
           into boolean values.
        """
        self.n2_seq_df[f'is_{subject}_sm_score_word_b'] = \
            (self.n2_seq_df.apply(
            lambda x: pd.Series(self.calc_similarity(self.glove_vectors, x['word_b'], subject)), axis=1
                ) > confidence
             ).values
        self.n2_seq_df[f'is_{subject}_sm_score_word_c'] = \
            (self.n2_seq_df.apply(
            lambda x: pd.Series(self.calc_similarity(self.glove_vectors, x['word_c'], subject)), axis=1
                ) > confidence
            ).values

    def compute_user_personal_state(self):
        """
        The purpose f this function is catch all of the important word. The similarity distance between
        every value from column b and c (since a has already been processed) with a given subject.
        The list of subjects is set at the init function. The function set a list of important words
        """
        final_df = pd.DataFrame(columns=self.n2_seq_df.columns)
        for sub in self.subjects:
            confidence = 0.7

            # compute similarity with confidence threshold and a subject
            self.compute_similarity_for_column(sub, confidence)

            # Ad rows with TRUE value
            temp_df = self.n2_seq_df[(self.n2_seq_df[f'is_{sub}_sm_score_word_b']) | (self.n2_seq_df[f'is_{sub}_sm_score_word_c'])]

            # Concat them to empty df
            final_df = pd.concat([final_df, temp_df])

            # Removed processed words so they won't be processed again
            self.n2_seq_df = self.n2_seq_df[~((self.n2_seq_df[f'is_{sub}_sm_score_word_b']) | (self.n2_seq_df[f'is_{sub}_sm_score_word_c']))]

        # If any of columns b contain TRUW values, get them, extract the value
        word_b_list = list(final_df[['word_b', 'is_disease_sm_score_word_b', 'is_medical_sm_score_word_b',
                                     'is_sickness_sm_score_word_b', 'is_physical_sm_score_word_b']][
                               (final_df['is_disease_sm_score_word_b'])
                               | (final_df['is_medical_sm_score_word_b'])
                               | (final_df['is_sickness_sm_score_word_b'])
                               | (final_df['is_physical_sm_score_word_b'])
                               ].word_b.values
                           )

        # If any of columns c contain TRUW values, get them, extract the value
        word_c_list = list(final_df[['word_c', 'is_disease_sm_score_word_c', 'is_medical_sm_score_word_c',
                                     'is_sickness_sm_score_word_c', 'is_physical_sm_score_word_c']][
                               (final_df['is_disease_sm_score_word_c'])
                               | (final_df['is_medical_sm_score_word_c'])
                               | (final_df['is_sickness_sm_score_word_c'])
                               | (final_df['is_physical_sm_score_word_c'])
                               ].word_c.values)

        # get the list of final important words
        self.user_personal_state_words = [*word_b_list, *word_c_list]

    def compute_personal_name(self):
        """
        Aim at replacing personal names in a given text (stored in self.prompt)
        with the name "John". using spaCy model.
        :return:
        """
        name_detector = spacy.load("en_core_web_sm")

        # Process the text with spaCy
        doc = name_detector(self.prompt)

        # Identify named entities
        for entity in doc.ents:
            if entity.label_ == "PERSON":
                print(entity.text)
                self.prompt = self.prompt.replace(entity.text, "John")

    def process_text(self):
        """
        The main function, it calls the relevant function in order to replace the relevant words.
        """
        start_time = time.time()

        # Replace name from the text
        self.compute_personal_name()

        # Create dictionary to track the actual word against the replacement word (if exist)
        for x in self.prompt.split(' '):
            x = x.replace(',','')
            self.msg_dict[x] = self.block_basic_personal_data(x)

        # Calls to the sequential function
        self.create_sequential_df()

        # Apply algorithm to find the sensitive words
        self.compute_user_personal_state()

        # Replace the value of the what the algorithm choose to be the sensitive
        for i in self.user_personal_state_words:
            self.msg_dict[i] = '#####'

        # Replace in the propmt text the sensitive words
        for word in self.prompt.split(' '):
            word = word.replace(',','')
            if self.msg_dict.get(str.lower(word),'not_found') != 'not_found':
                self.to_prompt+=self.msg_dict[str.lower(word)]+' '
            else:
                self.to_prompt +=word+' '
        end_time = time.time()
        logging.info(f"Personal detector elapsed time: {end_time - start_time:.4f} seconds")
