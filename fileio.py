import cmath, re

def get_header_data( data_file ):
	retval = dict()
	
	for line in data_file:
		line = lstrip( rstrip( line ) )
		
		if( line[0] != '$' ):
			match_obj = re.match( r"(.+)\s+=\s+(.+)", line )
			retval[match_obj.group(1)] = match_obj.group(2)
		else:
			if( line == '$END' ):
				end_count += 1
			
			if( end_count > 1 )
				return retval
			

def get_xy_data( data_file ):
	retval = list()
	
	for line in data_file:
		line = lstrip( rstrip( line ) )
		match_obj = re.match( r"(.+)\s+(.+)", line )
		retval.append( complex( match_obj.group(1), match_obj.group(2) ) )
		
	return retval

def main( argv ):
	data_file   = open( argv[0], 'r' )
	header_data = get_header_data( data_file )
	xy_data     = get_xy_data( data_file )

if __name__ == "__main__":
	sys.exit( main( sys.argv[1:] ) )

