from py2neo import Graph, Node
import os


password = os.getenv('NEO4J_PASSWORD')
user = os.getenv("NEO4J_USERNAME")
# graph = Graph(user=user, password=password)
graph = Graph("BlogTest", password="helloworld")



# Query
# CALL db.index.fulltext.queryNodes("articleContent", "query") YIELD node, score
# RETURN node.title, node.description, score

# graph.schema.create_uniqueness_constraint("User", "username")
# graph.schema.create_uniqueness_constraint("Article", "uuid")
# graph.schema.create_uniqueness_constraint("Comment", "uuid")
# graph.schema.create_uniqueness_constraint("Concept", "name")



def add_fts_index():
    query = """
         CALL db.index.fulltext.createNodeIndex("articleContent",["Article"],["title",
                                                                              "content",
                                                                              "author",
                                                                              "timestamp",
                                                                              "summary"])
    """
    graph.run(query)


def drop_fts_index():
    query = """
    """
    pass


# drop_fts_index()
# add_fts_index()
