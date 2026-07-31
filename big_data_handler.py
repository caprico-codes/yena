from extractor import Extractor

class BigDataHandler:
    def __init__(self, config):
        self.config = config['modules']['file_helper']
        self.extractor = Extractor()
        self.active_model = self.config['model']
        self.status = "READY"

    def process_file(self, file_path):
        """Loads full text and determines context tier based on token estimate."""
        text = self.extractor.get_text(file_path)
        
        # Heuristic: 1 token is roughly 4 characters
        token_estimate = len(text) / 4

        if token_estimate <= self.config['token_limit']:
            self.active_model = self.config['model']
            return text
        else:
            self.status = "TOO_LARGE"
            return None