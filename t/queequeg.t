# Test for queequeg.

use warnings;
use strict;
use Test::More;
use IPC::Run3;
use FindBin;

# The binary file which we run to do the tests.

my $binary = "$FindBin::Bin/../qq";
my @files = (qw!t2.txt!);

run3 ([$binary], \my $in, \my $out, \my $errors);
ok (! $errors);
for my $file (@files) {
    run3 ([$binary, "$FindBin::Bin/$file"], \my $in, \my $out, \my $errors);
    print "$errors\n";
    ok (! $errors);
}
done_testing ();
