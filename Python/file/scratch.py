import GENEActivFile as ga
import time


bin_file_path = (
    '/Users/kbeyer/repos/test_data/OND06_SBH_9248_01_SE01_GABL_GA_LA.bin')

pdf_path = (
    '/Users/kbeyer/repos/test_data/testout/')

ga_file = ga.GENEActivFile(bin_file_path)

print(f'reading {bin_file_path} ...')
ga_file.read()


start = time.time()

print('creating pdf...')
ga_file.create_pdf(pdf_path)


end = time.time()
print(end - start)


#print(f'parsing data ...')
#ga_file.view_data()




#print(ga_file.view_data(1,10))
#print(ga_file.view_data(2,10,update=False))

#print(ga_file.dataview.head())
#print(ga_file.dataview.shape)






