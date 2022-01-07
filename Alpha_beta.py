import copy
import numpy as np
import time
from numpy.lib.stride_tricks import as_strided

class GoBoard:
  def __init__(self, size):
    self.size=size
    self.currentstate=None
    self.prevstate=None
    self.moves=0
    self.max_move=24
    self.no_pass=0
  
  #Find the state in the dict
  def find_key(self, state):
    return ''.join([str(state[i][j]) for i in range(0,5) for j in range(0,5)])

  #Find members of same piece using BFS
  def find_same_piece(self, state, i, j, piece_type):
    queue=[(i,j)]
    same_piece_members=[]
    while queue:
      p=queue.pop()
      i=p[0]
      j=p[1]
      same_piece_members.append(p)
      n=[]
      if i>0 and state[i-1][j]==piece_type and (i-1,j) not in queue and (i-1,j) not in same_piece_members:
        queue.append((i-1,j))
      if i<self.size-1 and state[i+1][j]==piece_type and (i+1,j) not in queue and (i+1,j) not in same_piece_members:
        queue.append((i+1,j))
      if j>0 and state[i][j-1]==piece_type and (i,j-1) not in queue and (i,j-1) not in same_piece_members:
        queue.append((i,j-1))
      if j<self.size-1 and state[i][j+1]==piece_type and (i,j+1) not in queue and (i,j+1) not in same_piece_members:
        queue.append((i,j+1))
    return same_piece_members
  
  #Find the neighbors
  def find_neighbors(self, i, j, state):
    n=[]
    if i>0:
        n.append((i-1,j))
    if i<self.size-1:
        n.append((i+1,j))
    if j>0:
        n.append((i,j-1))
    if j<self.size-1:
        n.append((i,j+1))
    return n

  #Check all the liberty rules
  def find_liberty(self, state, i, j, piece_type):
    new_state=copy.deepcopy(state)
    new_state[i][j]=piece_type
    same_piece_members=self.find_same_piece(new_state, i, j, piece_type)
    for s in same_piece_members:
      neighbor=self.find_neighbors(s[0],s[1], state)
      for n in neighbor:
        if new_state[n[0]][n[1]]==0:
          return True
    return False
  
  #Check if any stone is captured while calculating the liberty
  def check_captured_stones(self, state, piece_type):
    opponent_piece=3-piece_type
    died_stones=[]
    for i in range(0,5):
      for j in range(0,5):
        if state[i][j]==opponent_piece:
          if not self.find_liberty(state, i, j, opponent_piece):
            died_stones.append((i,j))
    return died_stones
  
  #Remove the died stones of the opponent if any
  def remove_died_stones(self, died_stones, state):
    new_state=copy.deepcopy(state)
    for i in range(len(died_stones)):
        new_state[died_stones[i][0]][died_stones[i][1]]=0
    return new_state
  
  #Check for KO rule 
  def check_KO(self,prevstate,state, i, j):
    for i in range(0,5):
      for j in range(0,5):
        if prevstate[i][j]!=state[i][j]:
          return False
    return True
  
  #Check if a move is valid
  def check_valid_move(self, currstate, prevstate, i, j, piece_type):
    if i<0 or i>self.size-1 or j<0 or j>self.size-1:
      return False
    if currstate[i][j]!=0:
      return False
    
    if self.find_liberty(currstate, i, j, piece_type):
      return True
    else:
      new_state=copy.deepcopy(currstate)
      new_state[i][j]=piece_type
      died_stones=self.check_captured_stones(new_state, piece_type)
      new_state=self.remove_died_stones(died_stones, new_state)
      if not self.find_liberty(new_state, i, j, piece_type):
        return False
      elif self.check_KO(prevstate, new_state, i, j):
        return False

      return True

#Alpha-Beta Pruning upto depth 4
class AlphaBeta():
 def __init__(self):
   self.side=0
   self.init_board=[[0 for j in range(5)] for i in range(0,5)]
   self.max_depth=4
   self.type='AlphaBeta'
   self.black_groups=[]
   self.white_groups=[]
   self.no_pass=0
   self.go=GoBoard(5)
 
 def calc_liberties(self, currstate, prevstate):
   #Calculate black liberties
   b_l=[]
   w_l=[]
   black=0
   white=0
   for i in range(len(self.black_groups)):
     neighbors=self.go.find_neighbors(self.black_groups[i][0], self.black_groups[i][1], currstate)
     for j in range(len(neighbors)):
         if (neighbors[j][0], neighbors[j][1]) not in b_l:
           b_l.append((neighbors[j][0], neighbors[j][1]))
           black+=1
   #Calculate White liberties
   for i in range(len(self.white_groups)):
     neighbors=self.go.find_neighbors(self.white_groups[i][0], self.white_groups[i][1], currstate)
     for j in range(len(neighbors)):
         if (neighbors[j][0], neighbors[j][1]) not in w_l:
           w_l.append((neighbors[j][0], neighbors[j][1]))
           white+=1
   if self.side==1:
     return black-white
   else:
     return white-black
  
 #Identify the connected stones using Euler's number 
 def connected_stones(self, currstate, piece_type):
    q1=0
    q3=0
    qd=0
    arr = np.array(currstate)
    arr=np.pad(arr, pad_width=1)
    arr=np.where(arr==3-piece_type, 0, arr)
    two_quad = (2, 2)
    view_shape = tuple(np.subtract(arr.shape, two_quad) + 1) + two_quad
    state = as_strided(arr, view_shape, arr.strides * 2)
    state = state.reshape((-1,) + two_quad)
    for i in range(len(state)):
      if state[i][0][0]==piece_type and state[i][0][1]==state[i][1][0]==state[i][1][1]==0:
        q1+=1
      if state[i][0][1]==piece_type and state[i][0][0]==state[i][1][0]==state[i][1][1]==0:
        q1+=1 
      if state[i][1][0]==piece_type and state[i][0][1]==state[i][0][0]==state[i][1][1]==0:
        q1+=1
      if state[i][1][1]==piece_type and state[i][0][1]==state[i][1][0]==state[i][0][0]==0:
        q1+=1
      if state[i][0][1]==state[i][1][0]==state[i][1][1]==piece_type and state[i][0][0]==0:
        q3+=1
      if state[i][0][0]==state[i][1][0]==state[i][1][1]==piece_type and state[i][0][1]==0:
        q3+=1
      if state[i][0][0]==state[i][0][1]==state[i][1][1]==piece_type and state[i][1][0]==0:
        q3+=1
      if state[i][0][0]==state[i][1][0]==state[i][0][1]==piece_type and state[i][1][1]==0:
        q3+=1
      if state[i][0][0]==state[i][1][1]==piece_type and state[i][0][1] == state[i][1][0]==0:
        qd+=1
      if state[i][0][1]==state[i][1][0]==piece_type and state[i][0][0] == state[i][1][1]==0:
        qd+=1
      euler=(q1-q3+2*qd)/4
      return euler

 #Identify the coins in edges and corners
 def calculate_edges(self, currstate, piece_type):
   edges=0
   if currstate[0][0]==piece_type:
     edges+=1
   if currstate[0][4]==piece_type:
     edges+=1
   if currstate[4][0]==piece_type:
     edges+=1
   if currstate[4][4]==piece_type:
     edges+=1
   return edges

 #Calculate the utility value of all the leaf nodes
 def find_utility(self, currstate, prevstate, piece_type, max_captured, min_captured):
    white=0
    black=0
    for i in range(0,5):
      for j in range(0,5):
        if currstate[i][j]==1:
          black=black+1
          self.black_groups.append((i,j))
        elif currstate[i][j]==2:
          white=white+1
          self.white_groups.append((i,j))
    white=white+2.5
    liberty=self.calc_liberties(currstate, prevstate)
    black_eye=self.connected_stones(currstate, 1)
    white_eye=self.connected_stones(currstate, 2)
    self.black_groups=[]
    self.white_groups=[]
    bl_edges=self.calculate_edges(currstate, 1)
    w_edges=self.calculate_edges(currstate, 2)
    if piece_type==1:
      return 5*(black-white) + min(max(liberty,-4), 4) + (-4*(black_eye-white_eye)) - (bl_edges-w_edges) +(max_captured-min_captured)
    else:
      return white-black+min(max(liberty,-4), 4) + (-4*(white_eye-black_eye)) - (w_edges-bl_edges)+ (max_captured-min_captured)

 #MAX PLAYER
 def Max_value(self, currstate, prevstate, alpha, beta, depth, max_captured, min_captured):
   mac=0
   mic=0
   if depth==self.max_depth or self.no_pass==2:
     return (self.find_utility(currstate, prevstate, self.side, max_captured, min_captured), None)
   
   if depth==0 and currstate==self.init_board and self.side==1:
     return 0,(2,2)

   possible_move=False
   v=-np.inf
   action=None
   for i in range(0,5):
     for j in range(0,5):
       if self.go.check_valid_move(currstate, prevstate, i, j, self.side):
         possible_move=True
         if self.no_pass==1:
           self.no_pass=0
         new_state=copy.deepcopy(currstate)
         new_state[i][j]=self.side
         died_stones=self.go.check_captured_stones(new_state, self.side)
         if died_stones!=[]:
           max_captured+=len(died_stones)
           new_state=self.go.remove_died_stones(died_stones, new_state)

         v_new, a_new=self.Min_value(new_state, currstate, alpha, beta, depth+1, max_captured, min_captured)
         if v<v_new:
           v=v_new
           action=(i,j)

         alpha=max(v,alpha)
         if alpha>=beta:
           return v,action


   if possible_move!=True:
     self.no_pass+=1
     v_new, a_new=self.Min_value(currstate, currstate, alpha, beta, depth+1, max_captured, min_captured)
     if v<v_new:
       v=v_new 
     action="PASS"

   return v,action
 
 #MIN PLAYER
 def Min_value(self, currstate, prevstate, alpha, beta, depth, max_captured, min_captured):
   mac=0
   mic=0
   if depth==self.max_depth or self.no_pass==2:
     return (self.find_utility(currstate, prevstate, self.side, max_captured, min_captured), None)

   possible_move=False
   v=np.inf
   action=None
   for i in range(0,5):
     for j in range(0,5):
       if self.go.check_valid_move(currstate, prevstate, i, j, 3-self.side):
         if self.no_pass==1:
           self.no_pass=0
         possible_move=True
         new_state=copy.deepcopy(currstate)
         new_state[i][j]=3-self.side
         died_stones=self.go.check_captured_stones(new_state, 3-self.side)
         if died_stones!=[]:
           min_captured+=len(died_stones)
           new_state=self.go.remove_died_stones(died_stones, new_state)
         v_new, a_new=self.Max_value(new_state, currstate, alpha, beta, depth+1, max_captured, min_captured)
         if v>v_new:
           v=v_new
           action=(i,j)

         beta=min(v,beta)
         if alpha>=beta:
           return v_new, action

   if possible_move!=True:
     self.no_pass+=1
     v_new, a_new=self.Max_value(currstate, currstate, alpha, beta, depth+1, max_captured, min_captured)
     if v>v_new:
       v=v_new
     action="PASS"

   return v,action
 
  
 def get_input(self, go, side):
   self.side=side
   prev_state=go.previous_board
   curr_state=go.board
   self.go.currentstate=curr_state
   self.go.prevstate=prev_state
   alpha=-np.inf
   beta=np.inf
   start_time=time.time()
   v,action=self.Max_value(curr_state,prev_state,alpha,beta, 0, 0, 0)
   end_time=time.time()
   print("Time taken for move: ", end_time-start_time)
   return action
