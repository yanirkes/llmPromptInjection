from protection_layers import naive_protector

class NaiveSentanceProtector(naive_protector.NaiveProtector):
    """Get an input compound by multiple sentences and decomposed it to smaller sentences. Than
       it will use a naive approach.
    """
    def __init__(self, sensitivity_threshold = 0.83):
        super().__init__(sensitivity_threshold)

    def embed_sentance(self, sentance):
        return self.client.embeddings.create(
            input=sentance,
            model="text-embedding-ada-002"
        )

    def attack_score(self, sentance):
        embed_sentance = self.embed_sentance(sentance)
        import time
        time.sleep(10)
        return any(
                    list(
                        map(
                            lambda x: self.cosine_similarity(x, embed_sentance.data[0].embedding) > self.sensitivity_threshold,
                                self.malicious_embed_corpus
                            )
                        )
                   )

    def detect(self, sentences):
        """For each sentence calculate attack score"""
        are_sentence_is_attack = list(
            map(
                lambda sentence: self.attack_score(sentence), sentences
            )
        )
        return not any(are_sentence_is_attack)
