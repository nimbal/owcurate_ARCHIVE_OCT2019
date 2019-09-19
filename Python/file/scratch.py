import GENEActivFile as ga


bin_file_path = (
    '/Users/kbeyer/repos/test_data/OND06_SBH_9248_01_SE01_GABL_GA_LA.bin')

pdf_path = (
    '/Users/kbeyer/repos/test_data/testout/')

ga_file = ga.GENEActivFile(bin_file_path)

ga_file.read()
#ga_file.create_pdf(pdf_path, 4)

ga_file.view_data(1,10)

print(ga_file.dataview.head())
#print(ga_file.dataview.shape)

#print(ga_file.pagecount)
#print(ga_file.pagecount_match)


