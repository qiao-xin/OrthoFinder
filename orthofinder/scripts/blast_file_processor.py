# -*- coding: utf-8 -*-
#
# Copyright 2014 David Emms
#
# This program (OrthoFinder) is distributed under the terms of the GNU General Public License v3
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  
#  When publishing work that uses OrthoFinder please cite:
#      Emms, D.M. and Kelly, S. (2015) OrthoFinder: solving fundamental biases in whole genome comparisons dramatically 
#      improves orthogroup inference accuracy, Genome Biology 16:157
#
# For any enquiries send an email to David Emms
# david_emms@hotmail.com  

import sys
import csv
from scipy import sparse
          
def NumberOfSequences(seqsInfo, iSpecies):
    return (seqsInfo.seqStartingIndices[iSpecies+1] if iSpecies != seqsInfo.nSpecies-1 else seqsInfo.nSeqs) - seqsInfo.seqStartingIndices[iSpecies] 
                         
def GetBLAST6Scores(seqsInfo, fileInfo, iSpecies, jSpecies, qExcludeSelfHits = True, sep = "_"): 
    nSeqs_i = NumberOfSequences(seqsInfo, iSpecies)
    nSeqs_j = NumberOfSequences(seqsInfo, jSpecies)
    B = sparse.lil_matrix((nSeqs_i, nSeqs_j))
    row = ""
    try:
        with open(fileInfo.inputDir + "Blast%d_%d.txt" % (seqsInfo.speciesToUse[iSpecies], seqsInfo.speciesToUse[jSpecies]), 'rb') as blastfile:
            blastreader = csv.reader(blastfile, delimiter='\t')
            for row in blastreader:    
                # Get hit and query IDs
                try:
                    species1ID, sequence1ID = map(int, row[0].split(sep, 1)) 
                    species2ID, sequence2ID = map(int, row[1].split(sep, 1))     
                except (IndexError, ValueError):
                    sys.stderr.write("\nERROR: Query or hit sequence ID in BLAST results file was missing or incorrectly formatted.\n")
                    raise
                # Get bit score for pair
                try:
                    score = float(row[11])   
                except (IndexError, ValueError):
                    sys.stderr.write("\nERROR: 12th field in BLAST results file line should be the bit-score for the hit\n")
                    raise
                if (qExcludeSelfHits and species1ID == species2ID and sequence1ID == sequence2ID):
                    continue
                # store bit score
                try:
                    if score > B[sequence1ID, sequence2ID]: 
                        B[sequence1ID, sequence2ID] = score   
                except IndexError:
                    def ord(n):
                        return str(n)+("th" if 4<=n%100<=20 else {1:"st",2:"nd",3:"rd"}.get(n%10, "th"))
#                        sys.stderr.write("\nError in input files, expected only %d sequences in species %d and %d sequences in species %d but found a hit in the Blast%d_%d.txt between sequence %d_%d (i.e. %s sequence in species) and sequence %d_%d (i.e. %s sequence in species)\n" %  (nSeqs_i, iSpecies, nSeqs_j, jSpecies, iSpecies, jSpecies, iSpecies, sequence1ID, ord(sequence1ID+1), jSpecies, sequence2ID, ord(sequence2ID+1)))
                    sys.stderr.write("\nERROR: Inconsistent input files.\n")
                    kSpecies, nSeqs_k, sequencekID = (iSpecies,  nSeqs_i, sequence1ID) if sequence1ID >= nSeqs_i else (jSpecies,  nSeqs_j, sequence2ID)
                    sys.stderr.write("Species%d.fa contains only %d sequences " % (kSpecies,  nSeqs_k)) 
                    sys.stderr.write("but found a query/hit in the Blast%d_%d.txt for sequence %d_%d (i.e. %s sequence in species %d).\n" %  (iSpecies, jSpecies, kSpecies, sequencekID, ord(sequencekID+1), kSpecies))
                    sys.exit()
    except Exception:
        sys.stderr.write("Malformatted line in %sBlast%d_%d.txt\nOffending line was:\n" % (fileInfo.inputDir, seqsInfo.speciesToUse[iSpecies], seqsInfo.speciesToUse[jSpecies]))
        sys.stderr.write("\t".join(row) + "\n")
        sys.exit()
    return B  