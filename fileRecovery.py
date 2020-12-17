#A script to recover files in an input disk
#Supported file types are: MPG, PDF, BMP, GIF, ZIP, JPG, DOCX, AVI, PNG
#
#Created by Jacob Galanopoulos with review from Gus Tucker and Emma Mills
#Finalized 12/2/2020

import binascii, hashlib, re, sys
import os, os.path

try:
    diskFile = ''
    with open(sys.argv[1], 'rb') as diskFile:
        raw_bytes = binascii.hexlify(diskFile.read()).upper()
    diskFile.close()
    currentFileLength = 0
    allFiles = []
    weirdFiles = []
    currentFile = {
        'type': '',
        'contents': 0,
        'startOffset': '',
        'endOffset': '',
        'fileLength': '',
        'full': 0
    }
    #REGEX HELL
    lengthOfSector = 1024
    print("Size of disk: " + str(len(raw_bytes)/2097152) + "MB")
    for sector in range(0, len(raw_bytes), lengthOfSector): #Check every sector in order
        currentSectorinfo = raw_bytes[sector:sector+lengthOfSector] #slice out the 512 section of the string
        if (sector % 2097152 == 0):
            print("Checking " + str(sector/2097152) + " MB")
        if (currentFile['type'] == 'BMP'):
            headerMatch = re.findall("^(52494646([A-F0-9]{8})415649204C495354|424D|000001B|25504446|474946383761|474946383961|FFD8FF|504B030414000600|89504E470D0A1A0A|504B0304)", currentSectorinfo)
            reset = 0
            if (not(len(headerMatch) == 0)):
                print("File aborted for new file found")
                reset = 1
            elif (currentFileLength > 2097152): #Check if the BMP file is larger than 1MB. Should get rid of false posititves
                print("Max file size of BMP reached, aborting")
                reset = 1
            if(reset == 1):
                currentFile['length'] = currentFileLength
                currentFileLength = 0
                weirdFiles.append(currentFile)
                currentFile = {
                    'type': '',
                    'contents': 0,
                    'startOffset': '',
                    'endOffset': '',
                    'fileLength': '',
                    'full': 0
                }
        if (currentFile['contents'] == 0):
            #Check for a hit at the beginning of the files
            fileLengthMatch = re.findall("^(52494646([A-F0-9]{8})415649204C495354|424D)", currentSectorinfo) #should use regex to check for BMP or AVI files
            if (len(fileLengthMatch) == 0):
                #should use regex to check for all other supported files
                headerMatch = re.findall("^(000001B|25504446|474946383761|474946383961|FFD8FF|504B030414000600|89504E470D0A1A0A|504B0304)", currentSectorinfo)
                finalFooterLocation = 0
                if (len(headerMatch) == 0):
                    continue
                if headerMatch[0] == '000001B': #Get info for the MPG file
                    currentFile['type'] = 'MPG'
                    print(currentFile['type'] + ' file found!')
                    for match in re.finditer('(000001B7)', currentSectorinfo):
                        if ((match.end() % 2) == 0):
                            finalFooterLocation = match.end()
                elif headerMatch[0] == '25504446': #Get info for the PDF file
                    currentFile['type'] = 'PDF'
                    print(currentFile['type'] + ' file found!')
                    for match in re.finditer('(0A2525454F46|0A2525454F460A|0D0A2525454F460D0A|0D2525454F460D)', currentSectorinfo):
                        if (((match.end() % 2) == 0) and (currentSectorinfo[match.end()+2:match.end()+6] == '0000' or currentSectorinfo[match.end():match.end()+4] == currentSectorinfo[-4:])):
                            finalFooterLocation = match.end() #This may not work if it spreads over to a new sector and has this. Check the next sector if it has this as well
                elif headerMatch[0] == '474946383761': #Get info for the GIF 87a file
                    currentFile['type'] = 'GIF87a'
                    print(currentFile['type'] + ' file found!')
                    for match in re.finditer('(003B)', currentSectorinfo):
                        if (((match.end() % 2) == 0) and (currentSectorinfo[match.end()+2:match.end()+6] == '0000' or currentSectorinfo[match.end():match.end()+4] == currentSectorinfo[-4:])):
                            finalFooterLocation = match.end()
                elif headerMatch[0] == '474946383961': #Get info for the GIF 89a file
                    currentFile['type'] = 'GIF89a'
                    print(currentFile['type'] + ' file found!')
                    for match in re.finditer('(003B)', currentSectorinfo):
                        if (((match.end() % 2) == 0) and (currentSectorinfo[match.end()+2:match.end()+6] == '0000' or currentSectorinfo[match.end():match.end()+4] == currentSectorinfo[-4:])):
                            finalFooterLocation = match.end()
                elif headerMatch[0] == 'FFD8FF': #Get info for the JPEG file
                    currentFile['type'] = 'JPEG'
                    print(currentFile['type'] + ' file found!')
                    for match in re.finditer('FFD9', currentSectorinfo):
                        if (((match.end() % 2) == 0) and (currentSectorinfo[match.end()+2:match.end()+6] == '0000' or currentSectorinfo[match.end():match.end()+4] == currentSectorinfo[-4:])):
                            finalFooterLocation = match.end()
                elif headerMatch[0] == '504B030414000600': #Get info for the DOCX file
                    currentFile['type'] = 'DOCX'
                    print(currentFile['type'] + ' file found!')
                    for match in re.finditer('504B0506([A-F0-9]{36})', currentSectorinfo):
                        if ((match.end() % 2) == 0):
                            finalFooterLocation = match.end()
                elif headerMatch[0] == '89504E470D0A1A0A': #Get info for the PNG file
                    currentFile['type'] = 'PNG'
                    print(currentFile['type'] + ' file found!')
                    for match in re.finditer('49454E44AE426082', currentSectorinfo):
                        if (((match.end() % 2) == 0) and (currentSectorinfo[match.end()+2:match.end()+6] == '0000' or currentSectorinfo[match.end():match.end()+4] == currentSectorinfo[-4:])):
                            finalFooterLocation = match.end()
                elif headerMatch[0] == '504B0304': #Get info for the ZIP file
                    currentFile['type'] = 'ZIP'
                    print(currentFile['type'] + ' file found!')
                    for match in re.finditer('504B17([A-F0-9]{34})000000', currentSectorinfo):
                        if ((match.end() % 2) == 0):
                            finalFooterLocation = match.end()

                currentFile['startOffset'] = sector/2
                if not(finalFooterLocation == 0):
                    currentFile['endOffset'] = (sector+finalFooterLocation)/2
                    currentFile['contents'] = 1
                    currentFile['full'] = 1
                else:
                    currentFile['contents'] = 1
            else:
                if (fileLengthMatch[0][0] == '424D'): #Get info for the BMP file
                    currentFile['type'] = 'BMP'
                    print(currentFile['type'] + ' file found!')
                    fileLength = currentSectorinfo[8:10] + currentSectorinfo[6:8] + currentSectorinfo[4:6]
                    currentFileLength = int(fileLength, 16) * 2
                    print("BMP File length: " + str(currentFileLength))
                elif('52494646' in fileLengthMatch[0][0]): #Get info for the AVI file
                    currentFile['type'] = 'AVI'
                    print(currentFile['type'] + ' file found!')
                    fileLength = currentSectorinfo[14:16] + currentSectorinfo[12:14]+ currentSectorinfo[10:12]+ currentSectorinfo[8:10]
                    currentFileLength = (int(fileLength, 16) + 11) * 2
                    print("AVI File length: " + str(currentFileLength))
                else:
                    continue

                currentFile['startOffset'] = sector/2
                currentFile['fileLength'] = currentFileLength/2
                if (currentFileLength > lengthOfSector):
                    currentFile['contents'] = 1
                    currentFileLength -= lengthOfSector
                else:
                    currentFile['contents'] = 1
                    currentFile['endOffset'] = (sector+currentFileLength)/2
                    currentFileLength = 0
                    currentFile['full'] = 1
        else:
            #If we're here, that means there's a current file and we need to either check for a footer or grab data until the end of the file
            #If there's no footer, check for a header at the beginning of the file. This means we've got a corrupted file on our hands
            if (currentFile['type'] == 'AVI' or currentFile['type'] == 'BMP'): #Start grabbing until either the end of the sector or you get to the end
                if (currentFileLength > lengthOfSector):
                    currentFile['contents'] = 1
                    currentFileLength -= lengthOfSector
                else:
                    currentFile['contents'] = 1
                    currentFile['endOffset'] = (sector+currentFileLength)/2
                    currentFileLength = 0
                    currentFile['full'] = 1
            else: #Search for a footer. If there's no footer, check for a header at the beginning of the sector for broken files
                finalFooterLocation = 0
                if currentFile['type'] == 'MPG': #Get info for the MPG file
                    for match in re.finditer('(000001B7)', currentSectorinfo):
                        if ((match.end() % 2) == 0):
                            finalFooterLocation = match.end()
                elif currentFile['type'] == 'PDF': #Get info for the PDF file
                    for match in re.finditer('(0A2525454F46|0A2525454F460A|0D0A2525454F460D0A|0D2525454F460D)', currentSectorinfo):
                        if (((match.end() % 2) == 0) and (currentSectorinfo[match.end()+2:match.end()+6] == '0000' or currentSectorinfo[match.end():match.end()+4] == currentSectorinfo[-4:])):
                            finalFooterLocation = match.end() #This may not work if it spreads over to a new sector and has this. Check the next sector if it has this as well
                elif currentFile['type'] == 'GIF87a': #Get info for the GIF 87a file
                    for match in re.finditer('(003B)', currentSectorinfo):
                        if (((match.end() % 2) == 0) and (currentSectorinfo[match.end()+2:match.end()+6] == '0000' or currentSectorinfo[match.end():match.end()+4] == currentSectorinfo[-4:])):
                            finalFooterLocation = match.end()
                elif currentFile['type'] == 'GIF89a': #Get info for the GIF 89a file
                    for match in re.finditer('(003B)', currentSectorinfo):
                        if (((match.end() % 2) == 0) and (currentSectorinfo[match.end()+2:match.end()+6] == '0000' or currentSectorinfo[match.end():match.end()+4] == currentSectorinfo[-4:])):
                            finalFooterLocation = match.end()
                elif currentFile['type'] == 'JPEG': #Get info for the JPEG file
                    for match in re.finditer('FFD9', currentSectorinfo):
                        if (((match.end() % 2) == 0) and (currentSectorinfo[match.end()+2:match.end()+6] == '0000' or currentSectorinfo[match.end():match.end()+4] == currentSectorinfo[-4:])):
                            finalFooterLocation = match.end()
                elif currentFile['type'] == 'DOCX': #Get info for the DOCX file
                    for match in re.finditer('504B0506([A-F0-9]{36})', currentSectorinfo):
                        if ((match.end() % 2) == 0):
                            finalFooterLocation = match.end()
                elif currentFile['type'] == 'PNG': #Get info for the PNG file
                    for match in re.finditer('49454E44AE426082', currentSectorinfo):
                        if (((match.end() % 2) == 0) and (currentSectorinfo[match.end()+2:match.end()+6] == '0000' or currentSectorinfo[match.end():match.end()+4] == currentSectorinfo[-4:])):
                            finalFooterLocation = match.end()
                elif currentFile['type'] == 'ZIP': #Get info for the ZIP file
                    for match in re.finditer('504B17([A-F0-9]{34})000000', currentSectorinfo):
                        if ((match.end() % 2) == 0):
                            finalFooterLocation = match.end()

                if (not(finalFooterLocation == 0)):
                    currentFile['endOffset'] = (sector+finalFooterLocation)/2
                    currentFile['contents'] = 1
                    currentFile['full'] = 1
                else:
                    currentFile['contents'] = 1

        if (currentFile['full'] == 1):
            allFiles.append(currentFile)
            print(currentFile['type'] + ' file recovered!')
            currentFile = {
                'type': '',
                'contents': 0,
                'startOffset': '',
                'endOffset': '',
                'fileLength': '',
                'full': 0
            }
    print("\n==============================================================\n")
    print('The disk image contains ' + str(len(allFiles)) + ' files')
    fileCount = 1
    if (not(os.path.exists("RecoveredFiles"))):
        path = os.path.join("", "RecoveredFiles")
        os.mkdir(path)
    for file in allFiles:
        print('File' + str(fileCount) + '.' + file['type'] + ", Start Offset: " + hex(file['startOffset']) + " End Offset: " + hex(file['endOffset']))
        #So I stole this from another of my projects lol
        outputBytes = raw_bytes[(file['startOffset']*2):(file['endOffset']*2)-1].encode('utf-8')
        integrity = hashlib.sha256(outputBytes).hexdigest().upper()
        print("SHA-256: " + integrity + '\n')
        os.system("dd if=" + sys.argv[1] + " of=File" + str(fileCount) + "." + file['type'].lower() + " bs=1 skip=" + str(file['startOffset']) + " count=" +
            str(file['endOffset']-file['startOffset']) + " iflag=skip_bytes,count_bytes")
        os.system("mv File" + str(fileCount) + "." + file['type'].lower() + " RecoveredFiles")
        print("\n")
        fileCount += 1
    print("Recovered files are located in /RecoveredFiles in the current folder")
except OSError as error:
    print(error)
except TypeError as error:
    print(error)
except:
    print("Unexpected error:", sys.exc_info()[0])
