#importing dependencies
import json
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pydot
from networkx.drawing.nx_pydot import graphviz_layout
import random
from pyvis.network import Network
import os


class Graph:
  time_less_option=[3, 5, 8, 10] #time slots for questions with responses less than 5
  time_more_option=[12, 15, 20, 25, 30] #time slots for questions with responses greater than 5
  def __init__(self,data,category):
    ''' this is the default constructor to save data category, starting repsonse and ending response of the respective category'''
    
    self.data=data
    self.category=category[0]
    self.start=category[1][0]
    self.end=category[1][1]

  def graph_initialization(self):
    '''declares a directed graph for adding nodes and edges which ca be used for visualization'''
    
    self.G = nx.DiGraph()
    self.pre_process()
    
  def pre_process(self):
    '''This is the stage where the queue is added with the required questions and add the nodes to the graph'''
    
    self.time_taken=0
    for node in ['102','111']:
      resp=self.data["questions"][node]["responses"]#loading responses of question of the respective node
    
      self.time_taken+=random.choice(self.time_less_option)if len(resp)<5 else random.choice(self.time_more_option) # randomly choosing time according to number of responses presnt
        
      resp_ans=""
        
      for i in range(len(resp)):
        resp_ans+=str(i+1)+". "+resp[i]["prompt"]["text"]["1"]+"("+resp[i]["value"]+") \n" #converting the reponses into a form which can be stored as a title for the node in the graph

      # adding nodes to the graph with the created title(with questions and its respective options)
      self.G.add_node(node,title="Question: "+self.data["questions"][node]["prompt"]["text"]["1"]+"\nType: "+self.data["questions"][node]["type"]+"\nOptions: \n"+resp_ans)
      self.cal_time_taken()

      
  def cal_time_taken(self):
    ''' this function is used to process the data and find out the different nodes(qid's) and
    their respective paths associated to the questions ie.,"next" and form a network and calculate time taken for each question encountered'''
    
    visited_associated_symptoms_nodes={} #dict for keeping track of questions with "associated symptoms" title
    
    visited_nodes_in_queue={"112":True} #dict for keeping track of questions present in the queue


    self.traversed_nodes=["102","111"]  #list to keep track of nodes(questions ie., qid's) traversed

    que=["112"] #queue with first in last out rule to insert all the "next" occuring in the present questions
    
    compulsory_ques=['201','114'] #queue wth compulsory quesytions which are needed to be traversed
    while que:
      
      current_node=que.pop(0)
      
      if current_node=="83_11" or current_node=="94_6" or current_node=="86_8": continue #qid's which doesnt exist in the json

      # checking for the question with title as "Associated Symptoms" is visited or not
      if "Associated Symptoms" == self.data["questions"][current_node]["quesTag"]:
        
        if visited_associated_symptoms_nodes.get(current_node,False)!=False:
          continue
        
        visited_associated_symptoms_nodes[current_node]=True
      
      index=0 #index for placing the questions in an order
      
      responses=self.data["questions"][current_node]["responses"] #extracting responses of the current question
      
      self.time_taken+=random.choice(self.time_less_option)if len(responses)<5 else random.choice(self.time_more_option) # randomly choosing time according to number of responses presnt


      resp="" #converting the responses of the question to a form which can be stored as title of the node in the graph
      
      for i in range(len(responses)):
        resp+=str(i+1)+". "+responses[i]["prompt"]["text"]["1"]+"("+responses[i]["value"]+") \n" #converting the reponses into a form which can be stored as a title for the node in the graph

      
      self.traversed_nodes.append(current_node) #adding the current_node to the traversed node list

      #speacial case for qid "112" as it is where different categories arise
      if current_node=="112":
        if self.category!='Fever':
          for i in range(self.start,self.end):
            ''' checking wheather randomly generatted probaility is more than the threshold or not, if yes adding it to the queue and making it as visited'''
            
            if (random.randint(0, 10**5)/ 10**5)>=self.threshold_response:
              que.insert(i-self.start,str(i)+"_1") 
              visited_nodes_in_queue[str(i)+"_1"]=True
              
        else:
          '''this is the special case for fever cause it is having only one repsonse'''
          
          fev=['64_1','64_2','64_3','64_4','64_5','64_20']
          
          self.traversed_nodes.extend(fev)
          
          que.insert(0,'64_20')
          
          for ele in fev:
            responses=self.data["questions"][ele]["responses"]
            self.time_taken+=random.choice(self.time_less_option)if len(responses)<5 else random.choice(self.time_more_option) # randomly choosing time according to number of responses presnt
            
            resp=""
            for i in range(len(responses)):
              resp+=str(i+1)+". "+responses[i]["prompt"]["text"]["1"]+"("+responses[i]["value"]+") \n"
                
            self.G.add_node(ele,title="Question: "+self.data["questions"][ele]["prompt"]["text"]["1"]+"\nType: "+self.data["questions"][ele]["type"]+"\nOptions: \n"+resp)

        # the below code if for arranging the responses of question 112 because it is having 116 responses 
        
        resp=""
        for i in range(len(responses)):
          if i%4==0 and i!=0:
            resp+=str(i+1)+". "+responses[i]["prompt"]["text"]["1"]+"("+responses[i]["value"]+") \n"
          else:
            resp+=str(i+1)+". "+responses[i]["prompt"]["text"]["1"]+"("+responses[i]["value"]+")"+" "*5

        self.G.add_node(current_node,title="Question: "+self.data["questions"][current_node]["prompt"]["text"]["1"]+"\nType: "+self.data["questions"][current_node]["type"]+"\nOptions: \n"+resp)
        continue
      else:
        '''the below procedure is for the rest of the questions in the queue other than 112'''
        # checking wheather the question is skippable or not and checking wheather randomly generatted probaility is more than the threshold or not, if yes adding it to the queue and making it as visited
        if self.data["questions"][current_node]["skippable"]=="True" and (random.randint(0, 10**5)/ 10**5)>=self.threshold_question:
          
          #checking wheather there a next present in the question for all the reponses present like a global next
          if "next" in self.data["questions"][current_node].keys():
            
          # checking for the question's "next" is visited or not, if not it is added to the queue and visited_nodes_in_queue of the "next" is made True ie., visited
            if visited_nodes_in_queue.get(self.data["questions"][current_node]["next"],False)==False:
              
              que.insert(index,self.data["questions"][current_node]["next"])
              visited_nodes_in_queue[self.data["questions"][current_node]["next"]]=True
               
        '''checking wheather there a next present in the question's responses, if yes it is cheked if its is present in the queue already or not
        if not it is added to the queue and visited_nodes_in_queue of the "next" is made True ie., visited'''

        if any( "next" in response.keys() for response in responses):    
          for i in range(len(responses)):
              if "next" in responses[i].keys():
                ''' checking wheather randomly generatted probaility is more than the threshold or not, if yes adding it to the queue and making it as visited'''
                
                if (random.randint(0, 10**5)/ 10**5)>=self.threshold_response:
                  if visited_nodes_in_queue.get(responses[i]["next"],False)!=False:
                    continue
                  que.insert(index,responses[i]["next"])
                  visited_nodes_in_queue[responses[i]["next"]]=True
                  index+=1
                  
        # if the question is not skippable then it goes throught the same process about without any probability check          
        elif self.data["questions"][current_node]["skippable"]=="False":
          
          if "next" in self.data["questions"][current_node].keys():    
            if visited_nodes_in_queue.get(self.data["questions"][current_node]["next"],False)==False:
              
              que.insert(index,self.data["questions"][current_node]["next"])
              visited_nodes_in_queue[self.data["questions"][current_node]["next"]]=True
              
          if any( "next" in response.keys() for response in responses):
            for i in range(len(responses)):
                if "next" in responses[i].keys():
                  ''' checking wheather randomly generatted probaility is more than the threshold or not, if yes adding it to the queue and making it as visited'''
                  
                  if (random.randint(0, 10**5)/ 10**5)>=self.threshold_response:
                    if visited_nodes_in_queue.get(responses[i]["next"],False)!=False:
                      continue
                    que.insert(index,responses[i]["next"])
                    visited_nodes_in_queue[responses[i]["next"]]=True
                    index+=1
       
      #adding the current node to the graph with question and responses of the current question as the title
             
      self.G.add_node(current_node,title="Question: "+self.data["questions"][current_node]["prompt"]["text"]["1"]+"\nType: "+self.data["questions"][current_node]["type"]+"\nOptions: \n"+resp)

      #as the current node is present in the queue so it is deleted from the visited_nodes_in_queue
      if visited_nodes_in_queue.get(current_node,False):
        del visited_nodes_in_queue[current_node]

    #the below process is the same process as above while but this will be executed irespective of the above process and executes for the compusory quetions ie, feedback questions
    while compulsory_ques:
      current_node = compulsory_ques.pop(0)
      
      responses=self.data["questions"][current_node]["responses"]
      self.time_taken+=random.choice(self.time_less_option)if len(responses)<5 else random.choice(self.time_more_option) # randomly choosing time according to number of responses presnt
      index=0

      resp=""
      for i in range(len(responses)):
        resp+=str(i+1)+". "+responses[i]["prompt"]["text"]["1"]+"("+responses[i]["value"]+") \n"

      if "next" in self.data["questions"][current_node].keys():
          compulsory_ques.insert(index,self.data["questions"][current_node]["next"])
      if any( "next" in response.keys() for response in responses):
        
        for i in range(len(responses)):
            if "next" in responses[i].keys():
              ''' checking wheather randomly generatted probaility is more than the threshold or not, if yes adding it to the queue and making it as visited'''
              
              if (random.randint(0, 10**5)/ 10**5)>=self.threshold_response:
                compulsory_ques.insert(index,responses[i]["next"])
                index+=1
                
      self.traversed_nodes.append(current_node)
      self.G.add_node(current_node,title="Question: "+self.data["questions"][current_node]["prompt"]["text"]["1"]+"\nType: "+self.data["questions"][current_node]["type"]+"\nOptions: \n"+resp)
    self.add_edges()

    
  def add_edges(self):
    '''This fucntion is used to add edges from the derived traversed nodes'''
    
    edges=[]
    for i in range(len(self.traversed_nodes)-1):
      edges.append((self.traversed_nodes[i],self.traversed_nodes[i+1]))

    self.G.add_edges_from(edges) #adding nodes to the created directed graph
    self.viz_net()

    
  def viz_net(self):
    '''This function is used to visualize the graph created with nodes and edges '''
    
    net=Network(height='1000px', width='75%', bgcolor='#222222', font_color='white',notebook=True,directed=True) #creating a network class to load the graph
    net.from_nx(self.G) #creating a visual representation for the given graph
    net.show_buttons(filter_=['physics'])
    os.makedirs('graphs/'+self.category+"/"+str(self.threshold_question), exist_ok=True)  #creating a folder for the graph if not present
    net.show("graphs/"+self.category+"/"+str(self.threshold_question)+"/"+str(self.threshold_response)+".html") #saving the created plot of the graph

  def imp(self):
    ''' this function is used for ploting bar graphs for the time taken to fill the form with various combinations of threshold for question and responses'''
    
    os.makedirs('plots/'+self.category, exist_ok=True) #making a directory for storing the plots for the respective category
    plt.title("Time taken to fill the form for "+self.category)
    self.threshold_question=0
    ind=0
    
    while self.threshold_question<=0.3:
      self.threshold_response=0
      thres,time=[],[]
      
      while self.threshold_response<=0.8:
        
        thres.append(str(self.threshold_response))# storing the threshold for response for ploting the graph 
        self.graph_initialization() #calling the main fucntion
        time.append(round(self.time_taken/60,2)) # storing the time taken to fill the form for response for ploting the graph
        self.threshold_response+=0.1 #updating threshold_response
        self.threshold_response=float("%.2f" % self.threshold_response)
         
      # creating the bar plot
      plt.bar(thres, time)
      for i, t in enumerate(time):
          plt.text(i-0.2 , t, str(t)) #adding text values to the bar in the graph
      plt.xlabel("threshold_response(responses)")
      plt.ylabel("Time (min)")
      plt.title(str(self.threshold_question)+"(question)")
      ind+=1
        
      self.threshold_question+=0.05
      self.threshold_question=float("%.2f" % self.threshold_question)
      plt.savefig("plots/"+self.category+"/time_"+self.category+str(ind)+".jpeg") #storing thr graph plotted
      plt.clf()

def main():
  
  file = open('../../store.json')
  data = json.load(file) #loading the json
  os.makedirs('plots', exist_ok=True)
  categories=[["Ear_Nose_Throat",[12,45]],["Existing_health_condition",[45,54]],["Eye",[54,64]],["Fever",[64,65]],["genito_uninary",[65,80]],["Head",[80,88]],["Mental_health",[88,95]],["Respiratory",[95,102]],["Skin",[102,106]],["Stomach_problem",[106,116]]]
  print("Enter the option of category for which you need an edgelist and visual representation\n")
  for i in range(len(categories)):
    print(str(i+1)+". "+categories[i][0])
  category=int(input("Enter your choice: "))
  time_graph=Graph(data,categories[category-1])
  time_graph.imp()
  print("process completed!!")
  
 

if __name__=="__main__":
  main()

    
