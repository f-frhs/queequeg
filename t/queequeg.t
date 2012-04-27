# Test for queequeg.

use warnings;
use strict;
use Test::More;
use IPC::Run3;
use FindBin;

# The binary file which we run to do the tests.

my $binary = "$FindBin::Bin/../qq";

run3 ([$binary], \my $in, \my $out, \my $errors);
ok (! $errors);
done_testing ();
