#!/usr/bin/python
import atpy
import numpy as np
import make_table_lib as mkl
import plot_outcomes_lib as pol
import optparse
import copy

parser = optparse.OptionParser()

parser.add_option('-p', '--pref_cats',
	help='Enter names of matched cataloges, in order of preferable position')
	
parser.add_option('-m', '--matched_cats',
	help='Enter names of matched cataloges, in order of match')
	
parser.add_option('-c', '--cat_freqs', 
	help='Enter number of frequencies in each catalogue')
	
parser.add_option('-i', '--input_bayes', 
	help='Enter name of input matched bayes')

parser.add_option('-o', '--prob_thresh',
	help='The lower and upper probability thresholds - separate with a comma')

parser.add_option('-e', '--epsilon_thresh', 
	help='Cut-off threshold for the epsilon residuals')

parser.add_option('-x', '--chi_thresh', 
	help='Cut-off threshold for the chi squared residuals')

parser.add_option('-r', '--resolution', 
	help='Resolution of base catalogue in "deg:arcmin:arcsec" ie "00:03:00" for 3arcmins')

parser.add_option('-s', '--split',default=0, 
	help='The resolution ("deg:arcmin:arcsec") over which to split combined sources')

parser.add_option('-z', '--num_combinations', default=0,
	help='Plot the results of a certain number of combinations')

parser.add_option('-n', '--num_matches', default=0,
	help='Plot the results of a certain number of matches')

parser.add_option('-b', '--reject', action='store_true',default=False,
	help='Plot rejected sources')

parser.add_option('-d', '--eyeball', action='store_true',default=False,
	help='Plot sources to eyeball')

parser.add_option('-g', '--accept', action='store_true',default=False,
	help='Plot the accepted sources')

parser.add_option('-q', '--query', default='0',
	help='Plot the results of certain named sources')

options, args = parser.parse_args()

##Set up a bunch of initial parameters-----------------------------------------
##-----------------------------------------------------------------------------
plot_num_combs = int(options.num_combinations)
plot_num_matches = int(options.num_matches)

plot_reject = options.reject
plot_eyeball = options.eyeball
plot_accept = options.accept

if plot_accept==False and plot_eyeball==False and plot_reject==False:
	plot_all = True
else:
	plot_all = False
	
low_prob,high_prob = map(float,options.prob_thresh.split(','))
jstat_thresh = float(options.epsilon_thresh)
chi_thresh = float(options.chi_thresh)
closeness = mkl.dec_to_deg(options.resolution)/2

cat_fs = options.cat_freqs.split(',')
cat_freqs= []
for fs in cat_fs:
	split = fs.split('~')
	split = map(float,split)
	cat_freqs.append(split)

matched_cats = options.matched_cats.split(',')
pref_cats = ['weighted']
for pref in options.pref_cats.split(','): pref_cats.append(pref)
num_freqs = []
for freq in cat_fs: num_freqs.append(len(freq.split('~')))
split = options.split
queries = options.query.split(',')
##-----------------------------------------------------------------------------
##-----------------------------------------------------------------------------

##Transfer variables to the mkl and pol modules
pol.closeness = closeness
pol.high_prob = high_prob
pol.low_prob = low_prob
pol.chi_thresh = chi_thresh
pol.jstat_thresh = jstat_thresh
pol.num_freqs = num_freqs
pol.split = split
pol.matched_cats = matched_cats

mkl.closeness = closeness
mkl.high_prob = high_prob
mkl.low_prob = low_prob
mkl.chi_thresh = chi_thresh
mkl.jstat_thresh = jstat_thresh
mkl.num_freqs = num_freqs
mkl.split = split

def do_plot(comp,accepted_inds,match_crit,dom_crit,comb_crit,num_combs,truth_test,src_all):
	##Work out how many cataloges are present
	present_cats = [cat for cat in src_all.cats if cat!='-100000.0']
	num_matches = len(set(present_cats))
	if queries[0] == '0':
		if plot_all:
			if plot_num_matches == 0:
				if plot_num_combs == 0:
					pol.create_plot(comp,accepted_inds,match_crit,dom_crit,comb_crit)
				else:
					if num_combs == plot_num_combs: 
						pol.create_plot(comp,accepted_inds,match_crit,dom_crit,comb_crit)
					else:
						pass
			else:
				if num_matches == plot_num_matches:
					if plot_num_combs == 0:
						pol.create_plot(comp,accepted_inds,match_crit,dom_crit,comb_crit)
					else:
						if num_combs == plot_num_combs: 
							pol.create_plot(comp,accepted_inds,match_crit,dom_crit,comb_crit)
						else:
							pass
		else:
			if truth_test:
				if plot_num_matches == 0:
					if plot_num_combs == 0:
						pol.create_plot(comp,accepted_inds,match_crit,dom_crit,comb_crit)
					else:
						if num_combs == plot_num_combs: 
							pol.create_plot(comp,accepted_inds,match_crit,dom_crit,comb_crit)
						else:
							pass
				else:
					if num_matches == plot_num_matches:
						if plot_num_combs == 0:
							pol.create_plot(comp,accepted_inds,match_crit,dom_crit,comb_crit)
						else:
							if num_combs == plot_num_combs: 
								pol.create_plot(comp,accepted_inds,match_crit,dom_crit,comb_crit)
							else:
								pass
			else:
				pass
	else:
		for query in queries:
			if query in src_all.names: 
				pol.create_plot(comp,accepted_inds,match_crit,dom_crit,comb_crit)
			else: 
				pass

def single_match_test(src_all,comp,accepted_matches,accepted_inds,g_stats,num_matches,repeated_cats,matches):
	'''Takes a combination of sources, one from each catalogue, with positional probabilities,
	and determines whether they are a match or not - Algorithm 2 in the write up'''
	match = accepted_matches[0]
	prob = float(match[-1])
	##calculate_resids needs a list of matches - calculate parameters
	jstat_resids,params,bses,chi_resids = mkl.calculate_resids([match])
	src_g = mkl.get_srcg(match)
	
	##Play the prob trick again to work out which match has been accepted
	match_probs = [float(m.split()[-1]) for m in matches]
	dom_num = match_probs.index(prob)+1
	match_crit = "Combination (%d)\npossible\n%s repeated cats" %(dom_num,repeated_cats)
	
	##Check to see if all matched sources are within the closeness test - create an
	##error ellipse by combined closeness with base cat error
	##Need to convert closeness in to an RA offset, due to spherical trigonometry
	dr=np.pi/180.0
	delta_RA = np.arccos((np.cos(closeness*dr)-np.sin(src_all.decs[0]*dr)**2)/np.cos(src_all.decs[0]*dr)**2)/dr
	
	##Make a list of the ras and decs of the sources to distance test
	ras_test = [ra for ra in src_g.ras if ra!=-100000.0]
	dec_test = [dec for dec in src_g.decs if dec!=-100000.0]
	
	small_test = []
	for ra,dec in zip(ras_test,dec_test):
		##Even though at same dec, 3arcmis offset in RA isn't neccessarily 3arcmins arcdistance 
		ra_dist = mkl.arcdist(src_all.ras[0],ra,src_all.decs[0],src_all.decs[0])
		dec_dist = src_all.decs[0] - dec
		ra_axis = src_all.rerrs[0] + abs(delta_RA)
		dec_axis = src_all.derrs[0] + closeness

		##Test to see if the source lies with an error ellipse created using semi-major
		##and minor axes defined by the ra and dec error of the base cat + half the resolution
		##of the base cat (closeness)
		ell_test = (ra_dist/ra_axis)**2 + (dec_dist/dec_axis)**2
		if ell_test <= 1:
			small_test.append('yes')
		else:
			##Otherwise, fails
			small_test.append('no')
			#no_names.append(repeat_name)  #Note the name of the sources that are far away
	
	#Fail the positional test if a source is outside of the resolution plus position error
	close_test = 'passed'
	if 'no' in small_test: close_test = 'failed'
	
	##If prob is higher than threshold, ignore position of sources and accept the match
	if prob>high_prob:
		do_plot(comp,accepted_inds,match_crit,'N/A','Pos. accepted\nby $P>P_u$',num_matches,plot_accept,src_all)
	else:
		##look to see if all sources are within the resolution of the
		##base catalogue or above some probability theshold, if so check with a spec test else reject them
		if close_test=='passed' or prob>low_prob:  
			##IF below eith threshold, append with the applicable fit label
			if jstat_resids[0]<=jstat_thresh or chi_resids[0]<=chi_thresh:
				do_plot(comp,accepted_inds,match_crit,'Spec. passed','Accept by spec',num_matches,plot_accept,src_all)
			else:
				do_plot(comp,accepted_inds,match_crit,'Spec. failed','Reject by spec',num_matches,plot_reject,src_all)
		else:
			do_plot(comp,accepted_inds,match_crit,'N/A','pos reject by $P<P_l$',num_matches,plot_reject,src_all)

##Open the input text file (output from calculate_bayes.py)
bayes_comp = open(options.input_bayes).read().split('END_GROUP')
del bayes_comp[-1]

from matplotlib import rc
font = {'size': 14}
rc('font', **font)

for comp in bayes_comp:
	##Get the information into nice usable forms, and get rid of empty/pointless
	##entries
	chunks = comp.split('START_COMP')
	all_info = chunks[0].split('\n')
	
	##FOR SOME REASON CAN'T DO BOTH OF THESE LINES IN THE SAME FOR LOOP?!?!?!
	for entry in all_info:   
		if entry=='': del all_info[all_info.index(entry)]
	for entry in all_info:
		if 'START' in entry: del all_info[all_info.index(entry)]

	matches = chunks[1].split('\n')
	del matches[0],matches[-2:]
	
	##Put the information for every source in the matched group in one source_group() class
	##(see apply_criteria_lib for source_group())
	src_all = mkl.get_allinfo(all_info)
	
	##This line applies positional criteria, and tells us if a simple one catalogue repeat source, returning
	##how many combinations are possible and statistics on them
	repeated_cats,accepted_matches,accepted_inds,accepted_probs,jstats,chi_reds,g_stats = mkl.matches_retained(src_all,matches)
	match_crit = "%d of %d \ncombinations \npossible \n%s repeated cats" %(len(accepted_matches),len(matches),repeated_cats)
	
	##If no combinations are possible, reject all info (goes into the eyeball document)
	if len(accepted_matches)==0:
		do_plot(comp,accepted_inds,match_crit,'Positionally\nimpossible','N/A',len(matches),plot_reject,src_all)
		
	##If just one combo positionally possible, do a single combo check
	elif len(accepted_matches)==1:
		single_match_test(src_all,comp,accepted_matches,accepted_inds,g_stats,len(matches),repeated_cats,matches)
		##(Any plotting gets done within single_match_test)
		
	##If more than one combination is positionally possible:
	else:
		##Check for a dominant source. The combination must be the only one with high position prob,
		##all others with low positional proability, and must dominate spectrally
		dom_source = mkl.spec_pos_agree(jstats,chi_reds,accepted_probs)
		src_g = mkl.get_srcg(accepted_matches[0])
		##If it finds a dominant source, accept it - counts as a spectral match 
		if dom_source!='none':
			jstat_resids,params,bses,chi_resids = mkl.calculate_resids([accepted_matches[dom_source]])
			##Find the probs of all the matches, and use the prob of the dom match to see what number match was accepted
			all_probs = [float(match.split()[-1]) for match in matches]
			accepted_prob = accepted_probs[dom_source]
			dom_num = all_probs.index(accepted_prob)
			
			do_plot(comp,accepted_inds,match_crit,'Dom source (%d)' %(dom_num+1),'Accept dom.\nsource',len(matches),plot_accept,src_all)
			
		##If nothing dominates, send to check if a combined source works
		else:
			comb_crit, comb_source, comb_jstat, comb_chi_red = mkl.combine_flux(src_all,src_g,accepted_inds,'plot=no',len(matches))
			
			if 'Accepted' in comb_crit:
				do_plot(comp,accepted_inds,match_crit,'No dom. source',comb_crit,len(matches),plot_accept,src_all)
			else:
				do_plot(comp,accepted_inds,match_crit,'No dom. source',comb_crit,len(matches),plot_eyeball,src_all)