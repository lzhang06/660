
# coding: utf-8


import csv
from collections import OrderedDict
from datetime import datetime

class mylist(list):
    def __gt__(self, other):
        return [row_value > other for row_value in self]

l = mylist([1,23])

class DataFrame(object):

    @classmethod
    def from_csv(cls, file_path, delimiting_character=',', quote_character='"'):
        with open(file_path, 'rU') as infile:
            reader = csv.reader(infile, delimiter=delimiting_character, quotechar=quote_character)
            data = []

            for row in reader:
                data.append(row)

            return cls(list_of_lists=data)



    def __init__(self, list_of_lists, header=True):
        
        
        if header:
            self.header = list_of_lists[0]
            self.data = list_of_lists[1:]
        else:
            self.data = list_of_lists
            self.header = ['column' + str(index + 1) for index, column in enumerate(self.data[0])]


        self.data = [OrderedDict(zip(self.header, row)) for row in self.data]
    
    def __getitem__(self, item):
        # this is for rows only
        if isinstance(item, (int, slice)):
            return mylist(self.data[item])

        # this is for columns only
        elif isinstance(item, str):
            return mylist([row[item] for row in self.data])

        # this is for rows and columns
        elif isinstance(item, tuple):
            if isinstance(item[0], list) or isinstance(item[1], list):

                if isinstance(item[0], list):
                    rowz = [row for index, row in enumerate(self.data) if index in item[0]]
                else:
                    rowz = self.data[item[0]]

                if isinstance(item[1], list):
                    if all([isinstance(thing, int) for thing in item[1]]):
                        return mylist([[column_value for index, column_value in enumerate([value for value in row.values()]) if index in item[1]] for row in rowz])
                    elif all([isinstance(thing, str) for thing in item[1]]):
                        return mylist([[row[column_name] for column_name in item[1]] for row in rowz])
                    else:
                        raise TypeError('What the hell is this?')

                else:
                    return mylist([[value for value in row.items()][item[1]] for row in rowz])
            else:
                if isinstance(item[1],  slice) or isinstance(item[0], slice):
                    return mylist([[value for value in row.items()][item[1]] for row in self.data[item[0]]])
                
                elif isinstance(item[1], int):
                    return mylist([row for row in self.data[item[0]].items()][item[1]])
                
                
                elif isinstance(item[1], str):
                    return mylist(self[item[1]][item[0]])
                else:
                    raise TypeError('I don\'t know how to handle this...')

        # only for lists of column names A3-Task2
        elif isinstance(item, list):
            if isinstance(item[0], bool):
                if len(item) != len(self.data):
                    raise Exception("Slice length does not match data")
                else:
                    return mylist(self.data[i] for i in range(len(self.data)) if item[i])
            else:
                return mylist([[row[column_name] for column_name in item] for row in self.data])

        
     
        

        
    def get_rows_where_column_has_value(self, column_name, value, index_only=False):
        if index_only:
            return [index for index, row_value in enumerate(self[column_name]) if row_value==value]
        else:
            return [row for row in self.data if row[column_name]==value]
       
    #assignment3 
    #A3-task1
    def sort_by(self, column_name, aescending):
        if aescending == True:
            return sorted(self[column_name])
        else:
            return sorted(self[column_name], reverse = True)

           
    #A3-task3
    def group_by(self, column_name1, column_name2, func):
    
        inputs = self[[column_name1,column_name2]]
        inputs_dict = dict()
        avgDict = dict()
        for each in inputs:
            if each[0] in inputs_dict:
                inputs_dict[each[0]].append(each[1])
            else:
                inputs_dict[each[0]] = [each[1]] 
        for k, v in inputs_dict.items():
            avgDict[k] = func(v)
        return avgDict
        
def avg(list_of_values):       
    return sum(list_of_values)/float(len(list_of_values))

    
infile = open('/Users/Lucinda/Desktop/660/data_source/SalesJan2009.csv')
lines = infile.readlines()
lines = [lines[i].strip('\n') for i in range(len(lines))]
data = [l.split(',') for l in lines]
things = lines[559].split('"')
data[559] = things[0].split(',')[:-1] +[things[1]] + things[-1].split(',')[1:]
data[559][2] = data[559][2].replace(',','')

for p in range(1, len(data)):
    data[p][2] = float(data[p][2])
    data[p][0] = datetime.strptime(data[p][0], '%m/%d/%y %H:%M')

    
    

df = DataFrame(list_of_lists=data)
# get the 5th row
fifth = df[4]
sliced = df[4:10]

# get item definition for df [row, column]

# get the third column
tupled = df[:, 2]
tupled_slices = df[0:5, :3]

tupled_bits = df[[1, 4], [1, 4]]


# adding header for data with no header
#df = DataFrame(list_of_lists=data[1:], header=False)

# fetch columns by name
# named = df['column1']
# named_multi = df[['column1', 'column7']]

# #fetch rows and (columns by name)
# named_rows_and_columns = df[:5, 'column7']
# named_rows_and_multi_columns = df[:5, ['column4', 'column7']]


#testing from_csv class method
# df = DataFrame.from_csv('/Users/Lucinda/Desktop/660/data_source/SalesJan2009.csv')
# rows = df.get_rows_where_column_has_value('Payment_Type', 'Visa')
# indices = df.get_rows_where_column_has_value('Payment_Type', 'Visa', index_only=True)

# rows_way2 = df[indices, ['Product', 'Country']]


