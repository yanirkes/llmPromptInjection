from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, SequentialChain
import logging

class SemanticProtectorAdvance():

    def __init__(self, prompt):
        self.model_response = {}
        self.prompt = prompt
        self.analysis_chain = None
        self.response_chain = None
        self.embed_corpus(prompt)

    def embed_corpus(self, prompt):
        analysis_template = PromptTemplate(
            input_variables=['text'],
            template='write me a movie title about {text}'
        )

        response_template = PromptTemplate(
            input_variables=['title'],
            template='Between 0.0 to 1.0, does following has an average pattern or similarity to a movie title to you? {title}.'
                     'Please write the rate only'
        )

        # LLM
        llm = OpenAI(temperature=0.9)
        analysis_chain = LLMChain(llm=llm, prompt=analysis_template, verbose=True, output_key='title')
        response_chain = LLMChain(llm=llm, prompt=response_template, verbose=True, output_key='response')
        self.analysis_chain = analysis_chain
        self.response_chain = response_chain
        sequential_chain = SequentialChain(chains=[analysis_chain, response_chain], input_variables=['text'],
                                           output_variables=['response', 'title'], verbose=True)

        self.model_response = sequential_chain({'text': prompt})
        logging.info(f"LLM based model response: {self.model_response['response']}")

    def detect(self):
        return float(self.model_response['response']) > 0.4
