#!/home/ben/software/install/bin/perl
use warnings;
use strict;
my $dict = 'dict.txt';
my %dict;
open my $in, "<", $dict or die $!;
while (<$in>) {
    my ($left, $right) = split /\t/, $_, 2;
    my @right = split /,/, $right;
    $dict{$left} = \@right;
}
close $in or die $!;
