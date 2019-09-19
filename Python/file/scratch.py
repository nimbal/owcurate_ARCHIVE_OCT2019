import GENEActivFile as ga


bin_file_path = (
    '/Users/kbeyer/repos/test_data/OND06_SBH_9248_01_SE01_GABL_GA_LA.bin')

ga_file = ga.GENEActivFile(bin_file_path)

ga_file.read()

print(ga_file.pagecount)
print(ga_file.pagecount_match)


#ga_file.view_data(1,900)
