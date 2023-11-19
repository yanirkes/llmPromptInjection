import os
from apikey import apikey

import streamlit as st
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from protection_layers import protectors_mapper
import logging

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

os.environ['OPENAI_API_KEY'] = "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"
def main():
    os.environ['OPENAI_API_KEY'] = apikey

    # Set text and description
    st.title('Movies title generator')
    input = st.text_input('Please add only a topic, related to movie titles, you wish the system to generate for you.'
                           'Chose model.'
                           '1. naive'
                           '2. naive-multisentance'
                           '3. llm-based'
                           'write the the model name first, then the movie title, with \';\' as delimiter  (e.g naive; coffee house) '
                           )
    model_name, prompt = input.split(';') if len(input.split(';')) > 1 else  ('continue','')

    if model_name in ('naive','naive-multisentance','llm-based'):
        try:
            # Set subject such that the model would always be focus on generating from
            title_template = PromptTemplate(
                input_variables = ['topic'],
                template='write me a movie title about {topic}'
            )

            # LLM
            llm = OpenAI(temperature=0.9)
            title_chain = LLMChain(llm=llm, prompt=title_template, verbose = True)

            # Check prompt is valid. Than verify if model detected attack or prompt input is valid
            if prompt:
                # map between the different models
                to_prompt = protectors_mapper.ProtectorRouter.map_prompt(model_name, prompt)
                if to_prompt:
                    response = title_chain.run(topic=prompt)
                    st.write(response)
                    logging.info(f"Model response: {response}")
                else:
                    st.write('Attack found')
                    logging.info(f"Found model attack")

        except Exception as e:
            st.write('System reached to full capacity (3 prompts every 20 sec)')
            logging.exception('System reached to full capacity (3 pro`mpts every 20 sec)')
    else:
        st.write('Choose a proper model name')


if __name__ == "__main__":
    main()