from protection_layers import sentence_protector, llm_based_protector, naive_protector, llm_based_protector_advance, \
    personal_data_protection
import time
import logging


class ProtectorRouter(object):
    """
    A mapper that get from the user an input and route it to the corresponding protecting layer.
    """

    @classmethod
    def map_prompt(cls, model_name, prompt, glove_vectors=None):
        start_time = time.time()

        if model_name == 'naive':
            to_prompt = naive_protector.NaiveProtector(0.8).detect(prompt)
            end_time = time.time()
            logging.info(f"Naive model elapsed time: {end_time - start_time:.4f} seconds")

        elif model_name == 'naive-multisentance':
            sentences = prompt.split('.')
            sentence_protector_obj = sentence_protector.NaiveSentanceProtector(0.8)
            to_prompt = sentence_protector_obj.detect(sentences)
            end_time = time.time()
            logging.info(f"Multi sentance naive model Elapsed time: {end_time - start_time:.4f} seconds")

        elif model_name == 'llm-based':
            semantic_protector_obj = llm_based_protector.SemanticProtector(prompt)
            to_prompt = semantic_protector_obj.detect()
            end_time = time.time()
            logging.info(f"LLM based model elapsed time: {end_time - start_time:.4f} seconds")

        elif model_name == 'llm-based-adv':
            semantic_protector_obj = llm_based_protector_advance.SemanticProtectorAdvance(prompt)
            to_prompt = semantic_protector_obj.detect()
            end_time = time.time()
            logging.info(f"LLM advanced model elapsed time: {end_time - start_time:.4f} seconds")

        elif model_name == 'letter_layer':
            obj = personal_data_protection.PersonalDataProtector(prompt, glove_vectors)
            obj.process_text()
            to_prompt = obj.to_prompt

        time.sleep(5)
        return to_prompt
