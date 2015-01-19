#!/usr/bin/python
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import patches
from matplotlib.patches import Ellipse
from itertools import combinations
from astropy.wcs import WCS
from wcsaxes import WCSAxes
from astropy import units as units


##+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++	
##FOUR PLOTTING FUNCTIONS USED IN CREATE_PLOT -----------------------------------------------------------------------
def plot_errors(style,colour,freq,flux,ferr,name,size,ax):
	'''Plots errorbars and markers with no line'''
	ax.errorbar(freq,flux,ferr,
	marker=style,ms=size,mfc=colour,mec=colour,ecolor=colour,markeredgewidth=1,label=name,linestyle='None')
	
def plot_pos(style,colour,ra,dec,rerr,derr,name,size,ax,proj):
	'''Plots a single point with x and y erros bars'''
	if proj=='':
		p = ax.errorbar(ra,dec,derr,rerr,marker=style,ms=size,mfc=colour,mec=colour,ecolor=colour,markeredgewidth=1,label=name,linestyle='None')
	else:
		p = ax.errorbar(ra,dec,derr,rerr,marker=style,ms=size,mfc=colour,mec=colour,ecolor=colour,markeredgewidth=1,label=name,linestyle='None',transform=proj)
	return p
	
def plt_ell(ra,dec,height,width,PA,ax,colour,colour2,alpha,proj):
	'''Plots an ellipse - either plots on the ax_main which uses a wcs projection
	or on the smaller subplots which don't need transforming'''
	##Position Angle measures angle from direction to NCP towards increasing RA (east)
	##Matplotlib plots the angle from the increasing y-axis toward DECREASING x-axis
	##so have to put in the PA as negative
	if proj=='':
		ell = Ellipse([ra,dec],width=width,height=height,angle=-PA)
	else:
		ell = Ellipse([ra,dec],width=width,height=height,angle=-PA,transform=proj)  ##minus???
	ax.add_artist(ell)
	ell.set_alpha(alpha)
	ell.set_facecolor(colour)
	ell.set_edgecolor(colour2)
	
##POSSIBLE EXTENSION - MAKE GENERIC SO IT CYCLES THROUGH SOME COLOURS, NOT SPECIFIED COLOURS
##FOR A PARTICULAR CATALOGUE
def plot_all(cat,name,ra,rerr,dec,derr,major,minor,PA,ax,proj):
	'''Plots a position and an ellipse of specific colours/labels for known catalogues'''
	if cat=='mwacs':
		p = plot_pos('o','#660066',ra,dec,rerr,derr,cat+' '+name,8,ax,proj)     
		if PA!=-100000.0: 
			plt_ell(ra,dec,float(major),float(minor),float(PA),ax,'m','m',0.3,proj)
		##Plot an error ellipse
	elif cat=='sumss':
		name = name[5:]
		p = plot_pos('^','#990000',ra,dec,rerr,derr,cat+' '+name,8,ax,proj)
		if PA!=-100000.0: plt_ell(ra,dec,float(major),float(minor),float(PA),ax,'r','r',0.4,proj)
	elif cat=='nvss':
		p = plot_pos('x','#003300',ra,dec,rerr,derr,cat+' '+name,8,ax,proj)
		if PA!='--': plt_ell(ra,dec,float(major),float(minor),float(PA),ax,'g','#006600',0.5,proj)
	elif cat=='vlssr':
		name = name[5:]
		p = plot_pos('*','#000099',ra,dec,rerr,derr,cat+' '+name,8,ax,proj)
		if PA!=-100000.0: plt_ell(ra,dec,float(major),float(minor),float(PA),ax,'b','b',0.45,proj)
	elif cat=='mrc':
		p = plot_pos('h','y',ra,dec,(rerr),derr,cat+' '+name,8,ax,proj)
	elif cat=='culg':
		p = plot_pos('D','k',ra,dec,rerr,derr,cat+' '+name,8,ax,proj)
		if PA!=-100000.0:
			if minor!=-100000.0:
				if major!=-100000.0:
					plt_ell(ra,dec,float(major),float(minor),float(PA),ax,'k','k',0.4,proj) 
	elif cat=='askap':
		p = plot_pos('p','k',ra,dec,rerr,derr,name,8,ax,proj)
		#if PA!=-100000.0: plt_ell(ra,dec,float(major),float(minor),float(PA),ax,'k','k',0.4,proj)

##--------------------------------------------------------------------------------------------------------------------
def plot_ind(match,ax,ind_ax,ax_spectral,ra_bottom,ra_top,dec_bottom,dec_top,dom_crit,comb_crit):
	'''Takes a string of information of a particular combination and uses it
	to create a plot of the single combination, and fit and plot a line to
	the spectral information. Returns the positional probability, fitted paramaters
	and the residuals of the fit'''
	
	##Get the information from the particular match given
	info = match.split()
	indexes = [(14+((i-1)*3)) for i in num_freqs]
	starts = [0]
	for i in xrange(len(indexes)-1): starts.append(sum(indexes[:i+1]))
	fluxs = []
	freqs = []
	ferrs = []
	for j in xrange(len(starts)): 
		ind = starts[j]
		cat = info[ind]
		if cat!='-100000.0':
			freq = num_freqs[j]
			name = info[ind+1]
			ra = float(info[ind+2])
			rerr = float(info[ind+3])
			dec = float(info[ind+4])
			derr = float(info[ind+5])
			nu = float(info[ind+6])
			flux = float(info[ind+7])
			ferr = float(info[ind+8])/flux
			major = info[ind+9+((freq-1)*3)]
			minor = info[ind+10+((freq-1)*3)]
			PA = info[ind+11+((freq-1)*3)]
			fluxs.append(flux)
			freqs.append(nu)
			ferrs.append(ferr)
			##Plot each source on the individual combo plot
			plot_all(cat,name,ra,rerr,dec,derr,major,minor,PA,ax,'')
	##Sort the frequencies, fluxes and log them
	log_fluxs = np.log([flux for (freq,flux) in sorted(zip(freqs,fluxs),key=lambda pair: pair[0])])
	sorted_ferrs = np.array([ferr for (freq,ferr) in sorted(zip(freqs,ferrs),key=lambda pair: pair[0])])
	log_freqs = np.log(sorted(freqs))
	ferrs = np.array(ferrs)
	prob = info[-1]
	
	##Fit a line using weighted least squares and plot it
	lin_fit,jstat,bse,chi_red = fit_line(log_freqs,log_fluxs,sorted_ferrs)
	
	ax.text(0.5,0.925, 'P$_{%d}$=%.2f' %(ind_ax+1,float(prob)), transform=ax.transAxes,verticalalignment='center',horizontalalignment='center',fontsize=16)
	ax.text(0.5,0.06, '$\epsilon_{%d}$=%.2f $\chi_{%d}$=%.1f' %(ind_ax+1,jstat,ind_ax+1,chi_red),
		transform=ax.transAxes,verticalalignment='center',horizontalalignment='center',fontsize=16)
	
	ax.set_xlim(ra_bottom,ra_top)
	ax.set_ylim(dec_bottom,dec_top)
	
	##Plot RA backwards
	ax.invert_xaxis()
	
	##Plot the fitted spectral line, and return the plot object so we can create a legend from it
	if dom_crit=='No dom. source':
		if 'split' in comb_crit:
			spec_plot = 'na'
		else:
			spec_plot, = ax_spectral.plot(np.exp(log_freqs),np.exp(lin_fit.fittedvalues),linestyle='-',linewidth=1,alpha=0.3)
	else:
		spec_plot, = ax_spectral.plot(np.exp(log_freqs),np.exp(lin_fit.fittedvalues),linestyle='-',linewidth=1,alpha=1)
	
	return prob,jstat,spec_plot,lin_fit.params

def make_left_plots(fig,main_dims,spec_dims,ra_main,dec_main):
	
	##A fits image header with which to create a wcs with
	header = { 'NAXIS'  : 2,             ##Number of data axis
    'NAXIS1' : 10,                  ##Length of X axis
    'CTYPE1' : 'RA---SIN',           ##Projection type of X axis
	'CRVAL1' : ra_main,        ##Central X world coord value
	'CRPIX1' : 5,                    ##Central X Pixel value
	'CUNIT1' : 'deg',                ##Unit of X axes
	'CDELT1' : -0.001*np.cos(dec_main*(np.pi/180.0)),              ##Size of pixel in world co-ord
	'NAXIS2' : 10,                  ##Length of X axis
	'CTYPE2' : 'DEC--SIN',           ##Projection along Y axis
	'CRVAL2' : dec_main,                   ##Central Y world coord value
	'CRPIX2' : 5,                    ##Central Y Pixel value
	'CUNIT2' : 'deg',                ##Unit of Y world coord
	'CDELT2' : +0.001      		     ##Size of pixel in deg
	} 
	
	##Create the ws, and the main axis based on that. Plot top left
	wcs = WCS(header=header)
	ax_main = WCSAxes(fig, main_dims, wcs=wcs)
	fig.add_axes(ax_main)
	tr_fk5 = ax_main.get_transform("fk5")
	
	#ax_main.set_title("All sources within 3'.0")
	ax_main.text(0.01,0.93,"All sources within search area",verticalalignment='bottom',horizontalalignment='left', transform=ax_main.transAxes,fontsize=16)
	
	##Create bottom left plot with log-log axes - set the error bars to plot
	##even if they go off the edge of the plot
	ax_spectral = fig.add_axes(spec_dims)
	ax_spectral.set_xscale("log",nonposx='clip')
	ax_spectral.set_yscale("log",nonposy='clip')
	
	return ax_main,ax_spectral,tr_fk5,wcs

def fill_left_plots(all_info,ra_main,dec_main,ax_main,ax_spectral,tr_fk5,wcs,all_fluxs,ra_down_lim,ra_up_lim,dec_down_lim,dec_up_lim,delta_RA):
		##Get the information and plot the positions and fluxs on the left hand side plots
	ras = []
	decs = []
	all_freqs = []
	#all_fluxs = []
	all_ferrs = []
	#main_patches = []
	#main_labels = []
	for i in xrange(len(all_info)):
		info=all_info[i].split()
		cat = info[0]
		name = info[1]
		ra = float(info[2])
		ras.append(ra)
		rerr = float(info[3])
		dec = float(info[4])
		decs.append(dec)
		derr = float(info[5])
		major = info[-5]
		minor = info[-4]
		PA = info[-3]
		ID = info[-1]
		
		##If base catalogue, plot error and mathcing ellipses
		if i==0:
			
			error_RA = np.arccos((np.cos(closeness*dr)-np.sin(dec*dr)**2)/np.cos(dec*dr)**2)/dr
			
			###Plot an error ellipse of the base cat error + resolution
			#ell = patches.Ellipse((ra_main,dec_main),2*(rerr+closeness),2*(derr+closeness),angle=0,
				#transform=tr_fk5,linestyle='dashed',fc='none',lw=1.1,color='gray')
			#ax_main.add_patch(ell)
			
			##Plot an error ellipse of the base cat error + resolution
			ell = patches.Ellipse((ra_main,dec_main),2*(rerr+error_RA),2*(derr+closeness),angle=0,
				transform=tr_fk5,linestyle='dashed',fc='none',lw=1.1,color='gray')
			ax_main.add_patch(ell)
			
			###Plot a circle of the match radius
			ell = patches.Ellipse((ra_main,dec_main),2*delta_RA,4*(closeness),angle=0,
				transform=tr_fk5,linestyle='dashdot',fc='none',lw=1.1,color='k')
			ax_main.add_patch(ell)
		
		##Plot positions and elliptical fits
		plot_all(cat,name,ra,rerr,dec,derr,major,minor,PA,ax_main,tr_fk5)
		
		##See if one or more flux for a source, and plot fluxes with errorbars
		if len(info)==14:
			freq = float(info[6])
			flux = float(info[7])
			ferr = float(info[8])
			if cat=='mwacs':
				plot_errors('o','#660066',freq,flux,ferr,cat+' '+name,8,ax_spectral)
			elif cat=='sumss':
				plot_errors('^','#990000',freq,flux,ferr,cat+' '+name,9,ax_spectral)
			elif cat=='nvss':
				plot_errors('x','#003300',freq,flux,ferr,cat+' '+name,9,ax_spectral)
			elif cat=='vlssr':
				plot_errors('*','#000099',freq,flux,ferr,cat+' '+name,10,ax_spectral)
			elif cat=='mrc':
				plot_errors('h','y',freq,flux,ferr,cat+' '+name,10,ax_spectral)
			elif cat=='askap':
				plot_errors('p','k',freq,flux,ferr,cat+' '+name,10,ax_spectral)
			all_fluxs.append(flux)
			all_freqs.append(freq)
			all_ferrs.append(ferr)
		else:
			extra = (len(info)-14) / 3
			freqs = []
			fluxs = []
			ferrs = []
			for i in xrange(extra+1):
				freqs.append(info[6+(3*i)])
				fluxs.append(info[7+(3*i)])
				ferrs.append(info[8+(3*i)])
			if cat=='culg':
				if fluxs[0]!=-100000.0: plot_errors('D','k',float(freqs[0]),float(fluxs[0]),float(ferrs[0]),cat+' '+name+' 80MHz',4,ax_spectral)
				if fluxs[1]!=-100000.0: plot_errors('D','k',float(freqs[1]),float(fluxs[1]),float(ferrs[1]),cat+' '+name+' 160MHz',4,ax_spectral)
			for freq in freqs: all_freqs.append(float(freq))
			for flux in fluxs: all_fluxs.append(float(flux))
			for ferr in ferrs: all_ferrs.append(float(ferr))
				
	##Add some labels and coord formatting to ax_main
	ra_ax = ax_main.coords[0]
	dec_ax = ax_main.coords[1]
	ra_ax.set_axislabel('RAJ2000')
	dec_ax.set_axislabel('DECJ2000')
	ra_ax.set_major_formatter('hh:mm:ss')#,font='Computer Modern Typewriter')
	dec_ax.set_major_formatter('dd:mm:ss')
	
	##Convert axes limits to ax_main wcs, and apply
	ra_low = wcs.wcs_world2pix(ra_down_lim,dec_main,0)  ##The zero is for the orgin point of the image
	ra_high = wcs.wcs_world2pix(ra_up_lim,dec_main,0)
	dec_low = wcs.wcs_world2pix(ra_main,dec_down_lim,0)
	dec_high = wcs.wcs_world2pix(ra_main,dec_up_lim,0)
	ax_main.set_ylim(dec_low[1],dec_high[1])
	ax_main.set_xlim(ra_high[0],ra_low[0])

	###Add a grid with spacing of an arcmin
	#ra_ax.set_ticks(spacing=1 * units.arcmin)
	#dec_ax.set_ticks(spacing=1 * units.arcmin)
	#g = ax_main.coords.grid(linewidth=1.0,alpha=0.2)
	
	##Make the labels on ax_spectral print in MHz and Jy
	max_lflux = np.log(max(all_fluxs))
	min_lflux = np.log(min(all_fluxs))
	
	freq_ticks = [freq for freq in sorted(set(all_freqs))]
	flux_ticks = np.exp(np.arange(min_lflux,max_lflux+abs(max_lflux-min_lflux)/5,abs(max_lflux-min_lflux)/5))
	ax_spectral.set_xticks(freq_ticks,minor=False)
	ax_spectral.set_xticklabels(freq_ticks)
	ax_spectral.set_yticks(flux_ticks,minor=False)
	ax_spectral.set_yticklabels(['%.3f' %flux for flux in list(flux_ticks)],fontsize=14.0)

	##Set some limits on the spextral axis (work them out in log space)
	freq_min = 10**(np.log10(min(all_freqs))-0.1)
	freq_max = 10**(np.log10(max(all_freqs))+0.1)
	flux_min = 10**(np.log10(min(all_fluxs))-0.2)
	flux_max = 10**(np.log10(max(all_fluxs))+0.2)
	ax_spectral.set_xlim(freq_min,freq_max)
	ax_spectral.set_ylim(flux_min,flux_max)

	##Stick some grid stuff on the log log plot
	ten_steps = []
	for arr in [np.array([1e-5,2e-5,3e-5,4e-5,5e-5,6e-5,7e-5,8e-5,9e-5])*10**x for x in xrange(10)]:
		for i in list(arr): ten_steps.append(i)

	ax_spectral.set_xticks([step for step in ten_steps if step>freq_min and step<freq_max],minor=True)
	ax_spectral.set_yticks([step for step in ten_steps if step>flux_min and step<flux_max],minor=True)

	ax_spectral.xaxis.grid(True, which='minor',linestyle='dashed',alpha=0.1)
	ax_spectral.yaxis.grid(True, which='minor',linestyle='dashed',alpha=0.1)
	ax_spectral.set_xlabel(r'log$_{10}$(Frequency) (MHz)',fontsize=14)
	ax_spectral.set_ylabel(r'log$_{10}$(Flux) (Jy)',fontsize=14)
	

def create_plot(comp,accepted_inds,match_crit,dom_crit,outcome):
	
	###Split the information up as needed
	chunks = comp.split('START_COMP')
	all_info = chunks[0].split('\n')
	
	##FOR SOME REASON CAN'T DO BOTH OF THESE LINES IN THE SAME FOR LOOP?!?!?!
	for entry in all_info:   
		if entry=='': del all_info[all_info.index(entry)]
	for entry in all_info:
		if 'START' in entry: del all_info[all_info.index(entry)]

	matches = chunks[1].split('\n')
	del matches[0],matches[-2:]

	##See how many matches there are, and set up the number of plots needed
	num_matches = len(matches)
	if num_matches==1:
		width = 1
		height = 2
	else:
		width = int(num_matches**0.5)
		height = num_matches/width
		if num_matches%width==0:
			pass
		else:
			height+=1
	
	##Sets up a grid layout for the whole of the figure. We'll use half later on for
	##the individual plots
	gs = gridspec.GridSpec(height,2*width)
	
	##Need a big plot!
	fig = plt.figure(figsize = (20,15))

	##Find out the ra,dec of the base catalogue source
	info=all_info[0].split()
	ra_main = float(info[2])
	dec_main = float(info[4])
	
	main_dims = [0.1, 0.5, 0.28, 0.35]
	spec_dims = [0.1,0.1,0.28,0.35]
	
	ax_main,ax_spectral,tr_fk5,wcs = make_left_plots(fig,main_dims,spec_dims,ra_main,dec_main)
	
	##Find the limits out to search area - have to do each edge individual,
	##because of the arcdistance projection malarky
	##Even at the same dec, 3 arcmins apart in RA doesn't translate to 3arcmin arcdist - prpjection
	##fun. Can use law of cosines on a sphere to work out appropriate delta RA:
	
	delta_RA = np.arccos((np.cos((2*closeness)*dr)-np.sin(dec_main*dr)**2)/np.cos(dec_main*dr)**2)/dr
	
	plot_lim = (2*closeness) + (0.1/60.0)
	ra_up_lim = ra_main + delta_RA + (0.1/60.0)
	ra_down_lim = ra_main - delta_RA - (0.1/60.0)
	dec_up_lim = dec_main + plot_lim
	dec_down_lim = dec_main - plot_lim
	
	##Plot the individual combination plots - do this first so the error bars go over
	##the top of the line plots
	spec_labels = []
	SIs = []
	for i in xrange(height):
		for j in range(width,2*width):
			try:
				ind = (i*width)+(j-width)
				match = matches[ind]
				ax = plt.subplot(gs[i,j])
				ax.set_xticklabels([])
				ax.set_yticklabels([])
				prob,resid,spec_plot,params = plot_ind(match,ax,ind,ax_spectral,ra_down_lim,ra_up_lim,dec_down_lim,dec_up_lim,dom_crit,outcome)
				if spec_plot=='na':
					pass
				else:
					SIs.append([params[0],str(ind+1)])
					spec_labels.append(spec_plot)
			except IndexError:
				pass
	
	#===========================================================#
	##Plot the matching criteria information
	match1 = matches[0].split()
	src_g = get_srcg(match1)
	
	text_axes = fig.add_axes([0.39,0.5,0.125,0.35])
	text_axes.axis('off')

	##Plot the matching information
	props = dict(boxstyle='round', facecolor='w',lw='1.5')
	text_axes.text(0.5,0.5,'Match Criteria:\n%s\n\nDominace Test:\n%s\n\nOutcome:\n%s' %(match_crit,dom_crit,outcome),
		bbox=props,transform=text_axes.transAxes,verticalalignment='center',horizontalalignment='center',fontsize=18)
	
	all_fluxs = []
	
	##If no repeated catalogues to combine, skip
	if num_matches==0 or num_matches==1:
		pass
	##Otherwise, plot the combined fluxes
	else:
		##Calculate and plot the combined fluxes of the two sources, even if source one or two has been accepted
		##just as a guide
		src_all = get_allinfo(all_info)
		
		if accepted_inds=='Nope':
			pass
		else:
			comb_crit, ra_ws, rerr_ws, dec_ws, derr_ws, temp_freqs, comb_freqs, comb_fluxs, comb_ferrs, comb_fit, comb_jstat, comb_chi_red, combined_names, set_freqs, set_fluxs, set_fits = combine_flux(src_all,src_g,accepted_inds,'plot=yes',len(matches))
		
		##If the criteria sent the double to be combined, actually plot the fitted line
		if dom_crit == 'No dom. source':
			
			#for freq,flux in zip(set_freqs,set_fluxs):
				#ax_spectral.plot(freq,flux,linestyle='--',linewidth=1,color='r')
			
			split_colors = ['#AE70ED','#FFB60B','#62A9FF','#59DF00']
			for fit in set_fits:
				ind = set_fits.index(fit)
				ax_spectral.plot(set_freqs[ind],set_fluxs[ind],linestyle='--',linewidth=1.0,color=split_colors[ind],alpha=0.7)
				split_p, = ax_spectral.plot(temp_freqs,np.exp(fit.params[1] + np.log(temp_freqs)*fit.params[0]),linestyle='-',linewidth=1.5,color=split_colors[ind])
				spec_labels.append(split_p)
				SIs.append([fit.params[0],'split %d' %(ind+1)])
			
			bright_colours = ['#FF6600','#33FF33','#FF47A3']
			
			for freq in xrange(len(comb_freqs)):
				plot_errors('*',bright_colours[freq],comb_freqs[freq],comb_fluxs[freq],comb_ferrs[freq],'combo',9,ax_spectral)
			comb_p, = ax_spectral.plot(temp_freqs,np.exp(comb_fit.fittedvalues),linestyle='--',linewidth=1.5,color='k')
			spec_labels.append(comb_p)
			SIs.append([comb_fit.params[0],'comb'])
			
			##Send the combined fluxes to the all_fluxs so that ax_spectral is scaled appropriately
			for flux in comb_fluxs:
				all_fluxs.append(flux)
			
			for pos in xrange(len(ra_ws)):
				patch = plot_pos('*',bright_colours[pos],ra_ws[pos],dec_ws[pos],rerr_ws[pos],derr_ws[pos],combined_names[pos],10,ax_main,ax_main.get_transform("fk5"))

	##==============================================================

	##Fill the left hand plots with information goodness
	fill_left_plots(all_info,ra_main,dec_main,ax_main,ax_spectral,tr_fk5,wcs,all_fluxs,ra_down_lim,ra_up_lim,dec_down_lim,dec_up_lim,delta_RA)
	
	##Make room at the top of the plot for a legend for ax_main, make the legend
	fig.subplots_adjust(top=0.85)
	
	leg_labels = [r'$\alpha_{%s}$ = %.2f' %(SI[1],SI[0]) for SI in SIs]
	main_handles,main_labels = ax_main.get_legend_handles_labels()
	
	main_leg = fig.add_axes([0.05,0.87,0.9,0.05])
	main_leg.axis('off')
	main_leg.legend(main_handles,main_labels,loc='lower center',prop={'size':12},ncol=6) #,bbox_to_anchor=(0,1.02),
	
	spec_leg = fig.add_axes([0.39,0.1,0.125,0.35])
	spec_leg.axis('off')
	spec_leg.legend(spec_labels,leg_labels,loc='center',prop={'size':16},fancybox=True)
	
	plt.show()