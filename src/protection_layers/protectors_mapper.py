from protection_layers import sentence_protector, llm_based_protector, naive_protector, llm_based_protector_advance, personal_data_protection
import time
import logging

class ProtectorRouter(object):
    """
    A mapper that get from the user an input and route it to the corresponding protecting layer.
    """
    @classmethod
    def map_prompt(cls, model_name, prompt):
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
            to_prompt = personal_data_protection.PersonalLetterProtector().transform_letter(prompt)

        time.sleep(10)
        return to_prompt