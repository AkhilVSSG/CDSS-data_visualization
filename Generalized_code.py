#importing dependencies
import json
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pydot
from pyvis.network import Network
import os


class Graph:
  def __init__(self,data,category):
    self.data=data
    self.category=category[0]
    self.start=category[1][0]
    self.end=category[1][1]

  def Graph_initialization(self):
    '''declares a directed graph for adding nodes and edges which ca be used for visualization'''
    self.Directed_Graph = nx.DiGraph()
    print("Graph is initialized!!")
    self.pre_procesing()

  def pre_procesing(self):
    '''This is the stage where the queue is added with the required questions and add the nodes to the graph'''

    responses_102=self.data["questions"]["102"]["responses"] #loading responses of question qith qid "102"
    responses_102_text=""
    for i in range(len(responses_102)):
      responses_102_text+=str(i+1)+". "+responses_102[i]["prompt"]["text"]["1"]+"("+responses_102[i]["value"]+") \n" #converting the reponses into a form which can be stored as a title for the node "102" in the graph

    responses_111=self.data["questions"]["111"]["responses"] #loading responses of question qith qid "111"
    responses_111_text=""
    for i in range(len(responses_111)):
      responses_111_text+=str(i+1)+". "+responses_111[i]["prompt"]["text"]["1"]+"("+responses_111[i]["value"]+") \n" #converting the reponses into a form which can be stored as a title for the node "111" in the graph

    # adding nodes to the graph with the created title(with questions and its respective options)
    self.Directed_Graph.add_node("102",title="Question: "+self.data["questions"]["102"]["prompt"]["text"]["1"]+"\nType: "+self.data["questions"]["102"]["type"]+"\nOptions: \n"+responses_102_text)
    self.Directed_Graph.add_node("111",title="Question: "+self.data["questions"]["111"]["prompt"]["text"]["1"]+"\nType: "+self.data["questions"]["111"]["type"]+"\nOptions: \n"+responses_111_text)

    self.node_collection()

    
  def node_collection(self):
    ''' this function is used to process the data and find out the different nodes(qid's) and
    their respective paths associated to the questions ie.,"next" and form a network'''

    visited_associated_symptoms_nodes={} #dict for keeping track of questions with "associated symptoms" title
    
    visited_nodes_in_queue={"112":True,"201":True} #dict for keeping track of questions present in the queue

    self.traversed_nodes=["102","111"] #list to keep track of nodes(questions ie., qid's) traversed

    queue=["112","201"] #queue with first in last out rule to insert all the "next" occuring in the present questions

    while queue:
      current_node=queue.pop(0)
      if current_node=="83_11" or current_node=="94_6": continue #qid's which doesnt exist in the json
      
      # checking for the question with title as "Associated Symptoms" is visited or not
      if "Associated Symptoms" == self.data["questions"][current_node]["quesTag"]:    
        if visited_associated_symptoms_nodes.get(current_node,False)!=False:
          continue
        visited_associated_symptoms_nodes[current_node]=True
      
      index=0 #index for placing the questions in an order
      
      responses=self.data["questions"][current_node]["responses"] #extracting responses of the current question

      resp_text="" #converting the responses of the question to a form which can be stored as title of the node in the graph
      
      for i in range(len(responses)):
        resp_text+=str(i+1)+". "+responses[i]["prompt"]["text"]["1"]+"("+responses[i]["value"]+") \n"

      
      self.traversed_nodes.append(current_node)

      #speacial case for qid "112" as it is where different categories arise
      if current_node=="112":
        for i in range(self.start,self.end):
          queue.insert(i-self.start,str(i)+"_1")
          visited_nodes_in_queue[str(i)+"_1"]=True
        resp_text=""
        for i in range(len(responses)):
          '''below conditons are to just modify the spacing and alignment of the repsonses in the tile keeping 4 responses in one line
          and giving some space as there are 116 repsonses present'''

          if i%4==0 and i!=0:
            resp_text+=str(i+1)+". "+responses[i]["prompt"]["text"]["1"]+"("+responses[i]["value"]+") \n"
          else:
            resp_text+=str(i+1)+". "+responses[i]["prompt"]["text"]["1"]+"("+responses[i]["value"]+")"+" "*5

        #adding the current node to the graph with question and responses of the current question as the title
        self.Directed_Graph.add_node(current_node,title="Question: "+self.data["questions"][current_node]["prompt"]["text"]["1"]+"\nType: "+self.data["questions"][current_node]["type"]+"\nOptions: \n"+resp_text)
        continue

      else:
        #checking wheather there a next present in the question for all the reponses present like a global next
        if "next" in self.data["questions"][current_node].keys():
          # checking for the question's "next" is visited or not, if not it is added to the queue and visited_nodes_in_queue of the "next" is made True ie., visited
          if visited_nodes_in_queue.get(self.data["questions"][current_node]["next"],False)==False:
            queue.insert(index,self.data["questions"][current_node]["next"])
            visited_nodes_in_queue[self.data["questions"][current_node]["next"]]=True
            
        '''checking wheather there a next present in the question's responses, if yes it is cheked if its is present in the queue already or not
        if not it is added to the queue and visited_nodes_in_queue of the "next" is made True ie., visited'''
        
        if any( "next" in response.keys() for response in responses):
          for i in range(len(responses)):
            if "next" in responses[i].keys():          
              if visited_nodes_in_queue.get(responses[i]["next"],False)!=False:
                continue
              queue.insert(index,responses[i]["next"])
              visited_nodes_in_queue[responses[i]["next"]]=True
              index+=1
      #adding the current node to the graph with question and responses of the current question as the title
      self.Directed_Graph.add_node(current_node,title="Question: "+self.data["questions"][current_node]["prompt"]["text"]["1"]+"\nType: "+self.data["questions"][current_node]["type"]+"\nOptions: \n"+resp_text)

      #as the current node is present in the queue so it is deleted from the visited_nodes_in_queue
      if visited_nodes_in_queue.get(current_node,False):
        del visited_nodes_in_queue[current_node]
    
    print("nodes of the graph have been added!!")

    self.add_edges()
      

  def add_edges(self):
    '''This fucntion is used to add edges from the derived traversed nodes'''
    
    edges=[]
    for i in range(len(self.traversed_nodes)-1):
      edges.append((self.traversed_nodes[i],self.traversed_nodes[i+1]))

    self.Directed_Graph.add_edges_from(edges) #adding nodes to the created directed graph

    print("edges of the graph have been added!!")
    self.create_edgelist()
        
  def create_edgelist(self):
    '''This function is used to create an edgelist from the given graph'''
    os.makedirs(self.category+'/edgelist', exist_ok=True)  #creating a folder for the edgelist if not present
    nx.write_edgelist(self.Directed_Graph,self.category+"/edgelist/"+self.category+".edgelist",delimiter=' , ',data=False) #creating an edgelist from the directed graph and saving the file
    print("edgelist has been created!!")
    self.visualize_graph()

  def visualize_graph(self):
    '''This function is used to visualize the graph created with nodes and edges '''
    net=Network(height='1000px', width='75%', bgcolor='#222222', font_color='white',notebook=True,directed=True)#creating a network class to load the graph
    net.from_nx(self.Directed_Graph)#creating a visual representation for the given graph
    net.show_buttons(filter_=['physics'])
    os.makedirs(self.category+'/graph', exist_ok=True)  #creating a folder for the graph if not present
    net.show(self.category+"/graph/"+self.category+".html") #saving the created plot of the graph

    print("process for "+self.category+" has been completed!!")
    
def main():
  file = open('../store.json')
  data = json.load(file) #loading the json
  categories=[["Ear_Nose_Throat",[12,45]],["Existing_health_condition",[45,54]],["Eye",[54,64]],["Fever",[64,65]],["genito_uninary",[65,80]],["Head",[80,88]],["Mental_health",[88,95]],["Respiratory",[95,102]],["Skin",[102,106]],["Stomach_problem",[106,116]]]
  print("Enter the option of category for which you need an edgelist and visual representation\n")
  for i in range(len(categories)):
    print(str(i+1)+". "+categories[i][0])
  category=int(input("Enter your choice: "))
  output=Graph(data,categories[category-1])
  output.Graph_initialization()
  


if __name__=="__main__":
  main()

