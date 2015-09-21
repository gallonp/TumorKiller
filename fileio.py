#!/usr/bin/python

import cmath, re, sys

def get_header_data( data_file ):
	retval    = dict()
	end_count = 0
	
	for line in data_file:
		line = line.lstrip().rstrip()
		
		if( line[0] != '$' ):
			match_obj = re.match( r"(.+)\s+=\s+'?(.+)'?,?", line )
			retval[match_obj.group( 1 )] = match_obj.group( 2 ).rstrip( ',' ).rstrip( "'" )
		else:
			if( line == '$END' ):
				end_count += 1
			
			if( end_count > 1 ):
				return retval
			

'''
X/Y data:
X-axis = time
Y-axis = complex number
'''
def get_xy_data( data_file ):
	retval = list()
	
	for line in data_file:
		line = line.lstrip().rstrip()
		match_obj = re.match( r"(.+)\s+(.+)", line )
		retval.append( complex( float( match_obj.group(1) ), float( match_obj.group(2) ) ) )
		
	return retval

def main( argv ):
	data_file   = open( argv[0], 'r' )
	header_data = get_header_data( data_file )
	xy_data     = get_xy_data( data_file )
	
	for key, val in header_data.items():
		print( '{} = {}'.format( key, val ) )
	
	counter = 1
	
	for item in xy_data:
		print( '{} : {}'.format( counter, item ) )
		counter += 1

if __name__ == "__main__":
	sys.exit( main( sys.argv[1:] ) )

