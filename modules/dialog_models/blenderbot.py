from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, Conversation, ConversationalPipeline

class BlenderBot():

    def __init__(self):
        tokenizer = AutoTokenizer.from_pretrained("facebook/blenderbot-400M-distill")
        model = AutoModelForSeq2SeqLM.from_pretrained("facebook/blenderbot-400M-distill")
        self.nlp = ConversationalPipeline(model=model, tokenizer=tokenizer)
        self.conversation = Conversation()

    def add_input(self, text):
        self.conversation.add_user_input(text)
        result = self.nlp([self.conversation], do_sample=False, max_length=1000)
        messages = []
        for is_user, text in result.iter_texts():
            messages.append({
                'is_user': is_user,
                'text': text
            })
        return messages[-1]["text"]


