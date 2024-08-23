import logging
from pubsub import pub

# Setup for the general application logger
logger = logging.getLogger(__name__)
app_handler = logging.FileHandler('app.log')
app_handler.setLevel(logging.INFO)
app_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app_handler.setFormatter(app_formatter)
logger.addHandler(app_handler)
logger.setLevel(logging.INFO)

pub.setListenerExcHandler(logging.exception)

def setup_topics():
    pub.addTopicDefnProvider(TopicDefinitionProvider(), pub.TOPIC_TREE_FROM_CLASS)

class TopicDefinitionProvider:
    def getDefn(self, topicNameTuple):
        if topicNameTuple == ('opportunity_found',):
            return {'opportunity': "arbitrage opportunity found."}
        return None
