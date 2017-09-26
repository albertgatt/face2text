from generators import FrequencyDistGenerator, Phrase2VecGenerator,SimpleGenerator


ATT_LIST = ['Male', 'Bald', 'Bangs', 'Black_Hair', 'Blond_Hair', 
                'Blurry', 'Brown_Hair', 'Bushy_Eyebrows', 'Chubby', 'Double_Chin', 
                'Eyeglasses', 'Goatee', 'Gray_Hair', 'Heavy_Makeup', 'Mustache', 
                'Narrow_Eyes', 'No_Beard', 'Pale_Skin', 'Receding_Hairline', 
                'Rosy_Cheeks', 'Sideburns', 'Smiling', 'Straight_Hair', 'Wavy_Hair', 
                'Wearing_Hat', 'Wearing_Lipstick', 'Wearing_Necktie', 'Young']    

########################################################################
#Functions to generate descriptions in batch
########################################################################
def freq_generate_from_file(json_file, attributes):
    freqgen = FrequencyDistGenerator(json_file)    
    res = freqgen.generate(attributes)
    
    for (r, p) in res:
        print(r, p)

def sim_generate_from_file(json_file, vecpath, attributes):
    p2v = Phrase2VecGenerator(json_file, vecpath)        
    
    for (t, p) in p2v.generate(attributes):
        print(p, t, '\n')
    
    
def template_generate_from_file(sample_file, outfile): 
    generator = SimpleGenerator()  
    #generator.synonyms = False
    sep = '\t'   

    with open(sample_file, 'r', encoding='utf-8') as classifications:
        with open(outfile, 'w', encoding='utf-8') as output:
            for line in classifications.readlines():
                string_atts = [x.strip() for x in line.split(sep)]
                image = string_atts[0]
                attributes = {a:int(v) for (a,v) in zip(ATT_LIST, string_atts[1:])}
                phrase = generator.generate(attributes)                   
                output.write(image + "\t" + phrase + "\n") 


def generate_from_attributes(attributes, ignore_list):
    '''Takes a dictionary of attributes mapped to positive or negative values and returns a description'''
    generator = SimpleGenerator() #Instantiate a simple (template) generator  
    
    #Uncomment the below if we don't want to allow random synonym choice ('plump' for 'chubby', etc)
    generator.synonyms = True
    
        
    #Add things to this list that we NEVER want to use in a description
    generator.ignore_list = ignore_list
    
    #Run the generation
    description = generator.generate(attributes)
    return description
                    
                
#sim_generate_from_file('../output/goatee-glasses.json',  '../models/GoogleNews-vectors-negative300.bin', 'goatee glasses')  
#freq_generate_from_file('../output/goatee-glasses.json', 'goatee glasses')    
#template_generate_from_file('../output/attribute classifier - LFW Sample.txt', '../output/generated - LFW Sample 2.txt')

test_dict1 = {'Sideburns': 1.0, 'Black_Hair': 1.0, 'Wavy_Hair': -1.0,
                'Young': 1.0, 'Heavy_Makeup': 1.0, 'Blond_Hair': -1.0,
                'Wearing_Necktie': -1.0, 'Blurry': -1.0, 'Double_Chin': -1.0,
                'Brown_Hair': -1.0, 'Goatee': 1.0, 'Bald': 1.0, 'Gray_Hair':
                1.0, 'Pale_Skin': -1.0, 'Wearing_Hat': 1.0, 'Receding_Hairline':
                1.0, 'Straight_Hair': 1.0, 'Rosy_Cheeks': -1.0, 'Bangs': -1.0,
                'Male': 1.0, 'Mustache': 1.0, 'No_Beard': -1.0, 'Eyeglasses':
                -1.0, 'Wearing_Lipstick': 1.0, 'Narrow_Eyes': -1.0, 'Chubby':
                1.0, 'Smiling': 1.0, 'Bushy_Eyebrows': 1.0}
    
test_dict2 = {'Sideburns': -1.0, 'Black_Hair': 1.0, 'Wavy_Hair': -1.0,
                'Young': 1.0, 'Heavy_Makeup': 1.0, 'Blond_Hair': -1.0,
                'Wearing_Necktie': -1.0, 'Blurry': -1.0, 'Double_Chin': -1.0,
                'Brown_Hair': -1.0, 'Goatee': -1.0, 'Bald': 1.0, 'Gray_Hair':
                1.0, 'Pale_Skin': 1.0, 'Wearing_Hat': -1.0,
                'Receding_Hairline': 1.0, 'Straight_Hair': 1.0, 'Rosy_Cheeks':
                -1.0, 'Bangs': 1.0, 'Male': -1.0, 'Mustache': -1.0,
                'No_Beard': 1.0, 'Eyeglasses': -1.0, 'Wearing_Lipstick': 1.0,
                'Narrow_Eyes': -1.0, 'Chubby': -1.0, 'Smiling': 1.0,
                'Bushy_Eyebrows': 1.0}
    
test_dict3 = {'Wearing_Hat':1}
    
ignore_list = ['Blurry', 'Double_Chin', 'No_Beard', 'Narrow_Eyes'] 
print(generate_from_attributes(test_dict2, ignore_list))