from parse import *
from nltk.parse.corenlp import CoreNLPParser
import unittest


class MyTestCase(unittest.TestCase):
    def test_parse_for_multiple(self):
        sentence = "George and Mary ate dinner."
        parsed = next(CoreNLPParser().raw_parse(sentence))
        self.assertEqual(
            (parse_for(parsed, "NNP")[0].leaves()[0], parse_for(parsed, "NNP")[1].leaves()[0]),
            ("George", "Mary")
        )
        self.assertIsNone(parse_for(parsed, "NOPE"))

    def test_parse_for_q_to_a(self):
        # parse question
        question = "Where did Fred find the cookies?"
        q_parsed = next(CoreNLPParser().raw_parse(question))
        q_named = parse_for(q_parsed, "NNP")
        q_vp = parse_for(q_parsed, "VP")
        q_vb = parse_for(q_vp[0], "VB")
        q_obj = parse_for(q_vp[0], "NP")
        self.assertEqual(1, len(q_named))
        self.assertEqual("Fred", " ".join(q_named[0].leaves()))
        self.assertEqual(1, len(q_vp))
        self.assertEqual("find the cookies", " ".join(q_vp[0].leaves()))
        self.assertEqual(1, len(q_vb))
        self.assertEqual("find", " ".join(q_vb[0].leaves()))
        self.assertEqual(1, len(q_obj))
        self.assertEqual("the cookies", " ".join(q_obj[0].leaves()))

        # parse answer
        answer = "Fred found the cookies in the cupboard."
        a_parsed = next(CoreNLPParser().raw_parse(answer))
        a_named = parse_for(a_parsed, "NNP")
        a_vp = parse_for(a_parsed, "VP")
        a_vbd = parse_for(a_vp[0], "VBD")
        a_nps = parse_for(a_vp[0], "NP")
        a_pp = parse_for(a_vp[0], "PP")
        self.assertEqual(1, len(a_named))
        self.assertEqual("Fred", " ".join(a_named[0].leaves()))
        self.assertEqual(1, len(a_vp))
        self.assertEqual("found the cookies in the cupboard", " ".join(a_vp[0].leaves()))
        self.assertEqual(1, len(a_vbd))
        self.assertEqual("found", " ".join(a_vbd[0].leaves()))
        self.assertEqual(2, len(a_nps))
        self.assertEqual("the cookies", " ".join(a_nps[0].leaves()))
        self.assertEqual("the cupboard", " ".join(a_nps[1].leaves()))
        self.assertEqual(1, len(a_pp))
        self.assertEqual("in the cupboard", " ".join(a_pp[0].leaves()))

        # "find" (verify) answer of question
        self.assertEqual(q_named, a_named)
        # self.assertEqual(q_vbd, a_vbd)     # but past tense, though!
        self.assertEqual(q_obj[0], a_nps[0])
        # and PP is the answer, since we're dealing with "where"!

    def test_formulate_q(self):
        q = formulate_question("Did Fred give Lisa the memo?")
        self.assertEqual(
            Question(
                QuestionClass.POLAR,
                "Did",
                "give",
                "Fred",
                "Lisa",
                "memo"
            ),
            q
        )
        q = formulate_question("Was the monkey climbing the tree?")
        self.assertEqual(
            Question(
                QuestionClass.POLAR,
            ),
            q
        )
        q = formulate_question("Whose arrest was the cause for the riot?")
        self.assertEqual(
            Question(
                QuestionClass.WH,
            ),
            q
        )
        q = formulate_question("When are we moving to Canada?")
        self.assertEqual(
            Question(
                QuestionClass.WH,
            ),
            q
        )


if __name__ == '__main__':
    unittest.main()
