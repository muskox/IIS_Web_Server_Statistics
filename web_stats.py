# IIS Web Server Statistics
# by Scott Pustay
#
# Purpose
# -------
#
# This software reads a Microsoft Internet Information Services (IIS) V6.0 server log and finds 
# web statistics. It was written in Python 2.7.
#
# Input     IIS server log (in my example a partial month but full month logs work too)
#
# Output    HTML request/hits that are not from bots, spiders, crawlers, or slurps
#           GZ files downloaded from server 
#           Visitor Sessions (based on IP address and 30 minute time lag)
#           Unique IPs
#           Repeat Visitors (IP addresses that came back with a new session)
# 
# Extra Output with Reverse DNS enabled
#           Top Level Domains with counts for Unique domains
#           Unidentifed IPs

month_log = 'c:/ex1104_01partial.log' # TODO, make the file input from the command line.
enable_reverse_dns = 0 # enabling this takes much longer but give you more data

import fileinput, datetime, socket
from operator import itemgetter

# Declare some variables
html_hits = 0
files_downloaded = 0 
counter = 0
my_date_new = ''
my_date_old = ''

# unique_ips is a list of list, such as
# (['116.8.96.54', 1, ' 2011-04-01 00:03:51'], ['218.18.196.4', 5, '2011-04-09 04:03:51'])
# The first item is the IP address. The second item is the number of sessions this month
# the last item is time of last session.
unique_ips = []
# most requested pages. List of list similar to unique_ips. The list will be [[url, count],[url, count]]
most_requested_pages = []

for line in fileinput.input([month_log]):
    #print line
    section = line.split(' ')

    if len(section) > 9: # line 2 says #Version: 1.0 which makes section[2] null
        if len(section[0]) == 10: my_date_new = section[0] # make sure we're looking at a data ex '2011-07-27'
        if section[2] == 'GET':   
            in_html_section = 0
            in_gz_section = 0    
            # HTML section     
            if section[3][len(section[3])-5:] == '.html':
                in_html_section = 1
                # Don't include spiders
                # Known names, Baiduspider, speedy_spider
                # Googlebot, bingbot ezooms.bot, YandexBot, msnbot
                # Yahoo Slurp!, slurp
                if section[7].find('spider') > -1:
                    continue
                elif section[7].find('Spider') > -1:
                    continue
                elif section[7].find('bot') > -1:
                    continue
                elif section[7].find('Bot') > -1:
                    continue
                elif section[7].find('slurp') > -1:
                    continue
                elif section[7].find('Slurp') > -1:
                    continue
                elif section[7].find('crawler') > -1:
                    continue
                elif section[7].find('Crawler') > -1:
                    continue
                else:
                    html_hits = html_hits + 1  
                    # add this to most_requested_pages      
                    this_page_already_in_list = 0
                    for mrp in most_requested_pages:                        
                        if section[3] == mrp[0]: 
                            this_page_already_in_list = 1  
                            mrp[1] = mrp[1] + 1 # add a tally to the list
                            
                    # takes care of element 1        
                    if this_page_already_in_list == 0:
                        temp_list = [section[3], 1]             
                        most_requested_pages.append(temp_list)
            # GZ section               
            if section[3][len(section[3])-3:] == '.gz':
                files_downloaded = files_downloaded + 1 
                in_gz_section = 1    
            
            # IP addresses section
            this_one_already_in_the_list = 0
            
            if in_html_section == 1 | in_gz_section == 1:                  
                if len(unique_ips) == 0:      
                    temp_list = [section[6], 1, section[0] + ' ' + section[1]]           
                    unique_ips.append(temp_list)
            
                for ip in unique_ips:
                    if section[6] == ip[0]:
                        this_one_already_in_the_list = 1
                        # Check last session timestamp
                        # If less than 30 mins old, update ip[2] with new timestamp
                        # If over 30 mins old, update number of session ip[1] and update timestamp
                    
                        my_timestamp = ip[2].split(' ')
                        my_stored_date = my_timestamp[0].split('-')
                        my_stored_time = my_timestamp[1].split(':')                
                        stored_datetime = datetime.datetime(int(my_stored_date[0]), int(my_stored_date[1]), int(my_stored_date[2]), int(my_stored_time[0]), int(my_stored_time[1]), int(my_stored_time[2]))
                    
                        this_date = section[0].split('-')
                        this_time = section[1].split(':')
                        this_datetime = datetime.datetime(int(this_date[0]), int(this_date[1]), int(this_date[2]), int(this_time[0]), int(this_time[1]), int(this_time[2]))
                    
                        time_difference = this_datetime - stored_datetime
                        thirty_minutes = datetime.timedelta(minutes=30)
                    
                        if time_difference > thirty_minutes:
                            ip[1] = ip[1] + 1
                            ip[2] = section[0] + ' ' + section[1] 
                        else:
                            ip[2] = section[0] + ' ' + section[1]
                        
                if this_one_already_in_the_list == 0:
                    temp_list = [section[6], 1, section[0] + ' ' + section[1]]   
                    unique_ips.append(temp_list)
                
                  
        if not my_date_new == my_date_old: 
            print my_date_new
        my_date_old = my_date_new        
       

# with the unique_ips list, figure out total session visits and repeat visitors
total_sessions = 0
repeat_visitors = 0
unidentifed_ips = 0

top_tld = []
print 'Calculating Sessions totals'
if enable_reverse_dns == 1: 
    print ' and doing Reverse DNS lookups'
    print str(len(unique_ips)) + ' work units to complete'
ip_counter = 0
for ip in unique_ips:
    ip_counter = ip_counter + 1
    total_sessions = total_sessions + ip[1]
    if ip[1] > 1:
        repeat_visitors = repeat_visitors + 1
    
    if enable_reverse_dns == 1:  # this take much longer but give you more information on visitors
        if hasattr(socket, 'setdefaulttimeout'):
            # Set the default timeout on sockets to 5 seconds
            socket.setdefaulttimeout(5)        
            try:                  
                # find TLDs (top level domains)            
                the_last_dot = socket.gethostbyaddr(ip[0])[0].rindex('.')
                tld = socket.gethostbyaddr(ip[0])[0][the_last_dot+1:]
                tld_already_in_the_list = 0
                for tt in top_tld:
                    if tt[0] == tld:
                        tld_already_in_the_list = 1
                        tt[1] = tt[1] + 1
                                  
                if tld_already_in_the_list == 0:
                    temp_list = [tld, 1]
                    top_tld.append(temp_list)       
            except:
                unidentifed_ips = unidentifed_ips + 1
        
        if enable_reverse_dns == 1: print 'Units Completed: %d\r'%ip_counter,
           
print ''
print 'For File: ' + month_log
print 'HTML requests/hits:  ' + str(html_hits)
print 'GZ files downloaded: ' + str(files_downloaded)
print 'Visitor Sessions:    ' + str(total_sessions)
print 'Unique IPs:          ' + str(len(unique_ips))
print 'Repeat Visitors:     ' + str(repeat_visitors)

counter = 0
print ' '
print 'Most Popular Pages (first item is page, second item is count)'
popular_pages = sorted(most_requested_pages, key=itemgetter(1), reverse=True)
for pp in popular_pages:
    if counter < 10:
        print pp
    else:
        break    
    counter = counter + 1
 
if enable_reverse_dns == 1:  

    counter = 0
    print ' '
    print 'Top Level Domains with Counts'
    ordered_tld = sorted(top_tld, key=itemgetter(1), reverse=True)
    for ot in ordered_tld:
        if counter < 20:
            print ot
        else:
            break
        counter = counter + 1    
        
    print ' '  
    print 'Unidentifed IPs: ' + str(unidentifed_ips) 
