import gensim
from gensim import matutils

import numpy as np
from numpy import ndarray, float32, array, dot, mean


class Semantica:
    def __init__(self, model_path, word_count=1000000):
        self.c = gensim.models.KeyedVectors.load_word2vec_format(
            model_path, binary=True, limit=word_count)

    def unique(self, sequence):
        seen = set()
        return [x for x in sequence if not (x in seen or seen.add(x))]

    def to_lower(self, concepts):
        for i in range(len(concepts)):
            concepts[i] = concepts[i].lower()

        return self.unique(concepts)

    def to_vector(self, concept, norm=True):
        """Turn a concept key or concept vector into a concept vector.

        If `concept` is a vector, return it. If it's a key, return the associated vector after optionally normalizing it.
        """
        if isinstance(concept, ndarray):
            return concept
        else:
            if norm:
                return matutils.unitvec(self.c.get_vector(concept))
            else:
                return self.c.get_vector(concept)

    def field(self, concept, norm_concept=True, lower=True):
        """Return the semantic field of a given concept key or vector.

        Extract the concept keys most similar to `concept` after optionally normalizing it, and return them.
        """
        field = self.c.most_similar([self.to_vector(concept, norm=norm_concept)], topn=10)
        field = [e[0] for e in field]

        if lower:
            lower_unique_results = self.to_lower(field)
        else:
            lower_unique_results = field

        if isinstance(concept, str):
            new_results = [e for e in lower_unique_results if str(e) != str(concept)]
        else:
            new_results = lower_unique_results

        return new_results

    def mix(self, *concepts, shift=None, norm_concepts=True, norm_result=True, lower=True):
        """Combine the meaning of multiple concepts.

        Average the vectors associated with the given concepts and return the normalized result.
        """
        concept_vectors = []

        for concept in concepts:
            concept_vectors += [self.to_vector(concept, norm=norm_concepts)]

        if shift is not None:
            concept_vectors += [self.shift(shift[0], shift[1], norm_concepts=False, norm_result=True)]

        mix = array(concept_vectors).mean(axis=0).astype(float32)

        results = self.field(mix, norm_concept=norm_result, lower=lower)
        
        if lower:
            lower_unique_results = self.to_lower(results)
        else:
            lower_unique_results = results

        new_results = [e for e in lower_unique_results if e not in concepts]

        if shift is not None:
            new_results = [e for e in new_results if e not in shift]

        return new_results

    def shift(self, source, target, norm_concepts=True, norm_result=True):
        """Return a vector which encodes a meaningful semantic shift.

        Compute the difference between a source and target vector, and return the normalized result.
        """
        source_vector = -1 * self.to_vector(source, norm=norm_concepts)
        target_vector = self.to_vector(target, norm=norm_concepts)

        shift = array([source_vector, target_vector]).mean(axis=0).astype(float32)

        if norm_result:
            shift = matutils.unitvec(shift)

        return shift

    def span(self, start, end, steps=5, norm_concepts=False, norm_shift_result=False, norm_result=False, norm_mix_concepts=True):
        """Return an interpolation of the semantic space between two concepts.

        
        """
        step_keys = []
        shift = self.shift(start, end, norm_concepts=norm_concepts, norm_result=norm_shift_result)

        for step in range(1, steps + 1):
            step_key_field = self.mix(*[start, shift * (1 / steps) * step], norm_result=norm_result, norm_concepts=norm_mix_concepts, lower=False)
            step_keys += [*step_key_field]

        step_keys = sorted(step_keys, key=lambda x: self.c.rank(x, start)/self.c.rank(x, end))

        lower_unique_results = self.to_lower(step_keys)
        new_results = [e for e in lower_unique_results if e != start.lower() and e != end.lower()]

        return new_results

    def model(self, model, match_threshold=0.6):
        root = model[0]
        skeleton = [self.shift(root, e, norm_concepts=False, norm_result=False) for e in model[1:]]
        matches = []

        for i in range(len(self.c.vectors)):
            match_score = []
            new_leaf_concepts = []

            new_root_vector = self.c.vectors[i]
            new_leaf_vectors = [
                self.mix(new_root_vector, skeleton[j]) for j in range(len(skeleton))]

            new_root_concept = self.c.similar_by_vector(new_root_vector)[0][0]
            new_leaf_concepts = []

            for new_leaf_vector in new_leaf_vectors:
                new_leaf_concept = [e[0] for e in self.c.similar_by_vector(
                    new_leaf_vector) if e[0] not in [new_root_concept, *new_leaf_concepts]][0]
                new_leaf_concepts += [new_leaf_concept]

            for i in range(len(new_leaf_vectors)):
                match_score += [dot(self.shift(new_root_concept,
                                               new_leaf_concepts[i]), skeleton[i])]

            #for i in range(len(new_leaf_vectors)):
            #    match_score += [dot(matutils.unitvec(new_leaf_vectors[i]),
            #                        matutils.unitvec(self.to_vector(new_leaf_concepts[i])))]

            # if "man" in [e[0] for e in self.c.similar_by_vector(new_root)]:
            #    print('---', [e for e in [self.c.similar_by_vector(e) for e in [new_root] + new_leafs]], sep='\n')

            match_score = mean(match_score)

            if match_score > match_threshold:
                match = [new_root_concept, *new_leaf_concepts]
                #matches += [new_root, *new_leafs]
                print('---', *self.field(match), sep='\n')
                print(match_score)
