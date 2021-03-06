'''
Created on 8 Feb 2017

@author: ian
'''

import argparse
import sys
from lxml.etree import Element, SubElement, tostring, QName



# import dicttoxml
# from xml.dom.minidom import parseString

import lxml.etree as ET
import os


class XQName(QName):
    def __init__(self,uri,tag=None):
        if tag is None:
            tag = uri
        super(QName, self).__init__(self,uri,tag)
        if uri is None:
            self.uri = tag
        elif tag is None:
            self.tag = uri
        else:
            self.text = '{'+uri+'}'+tag

    
class xml_to_sld(object):

    def set_color(self, target, color):
        colors = []
        colors.append(color.get('red'))
        colors.append(color.get('green'))
        colors.append(color.get('blue'))
        target.text = "#" + "".join("{:02X}".format(int(a)) for a in colors)


    def getStroke(self, style, symbol, isLine=False):
        color = style.find('{http://www.mapserver.org/mapserver}outlineColor')
        if isLine:
            color = style.find('{http://www.mapserver.org/mapserver}color')
        if color is None:
            #nothing doing here
            return
        else:
            stroke = ET.SubElement(symbol, "Stroke")
            stroke_color = ET.SubElement(stroke, "CssParameter", name="stroke")
            self.set_color(stroke_color, color)
        
        width = style.find('{http://www.mapserver.org/mapserver}outlineWidth')
        if width is None:
            width = style.find('{http://www.mapserver.org/mapserver}width')
        if width is not None:
            stroke_width = ET.SubElement(stroke, "CssParameter", name="stroke-width")
            stroke_width.text = width.text
        line_cap = style.find('{http://www.mapserver.org/mapserver}lineCap')
        if line_cap is not None:
            stroke_cap = ET.SubElement(stroke, "CssParameter", name="stroke-linecap")
            stroke_cap.text = line_cap.text
        line_join = style.find('{http://www.mapserver.org/mapserver}lineJoin')
        if line_join is not None:
            stroke_join = ET.SubElement(stroke, "CssParameter", name="stroke-linejoin")
            stroke_join.text = line_join.text
        line_dash = style.find('{http://www.mapserver.org/mapserver}pattern')
        if line_dash is None:
            line_dash = style.find('{http://www.mapserver.org/mapserver}gap')
        if line_dash is not None:
            stroke_dash = ET.SubElement(stroke, "CssParameter", name="stroke-dasharray")
            stroke_dash.text = line_dash.text
        line_gap = style.find('{http://www.mapserver.org/mapserver}initialGap')
        if line_gap is not None:
            stroke_offset = ET.SubElement(stroke, "CssParameter", name="stroke-dashoffset")
            stroke_offset.text = line_gap.text
        #ET.dump(stroke)

    def getFill(self, style, symb):
        color = style.find('{http://www.mapserver.org/mapserver}color')
        if color is None:
            return
        fill = ET.SubElement(symb, "Fill")
        if color is not None:
            fill_color = ET.SubElement(fill, "CssParameter", name="fill")
            self.set_color(fill_color, color)
        opacity = style.find('{http://www.mapserver.org/mapserver}opacity')
        if opacity is not None:
            fill_opacity = ET.SubElement(fill,"CssParameter", name="fill-opacity")
            fill_opacity.text = str(float(opacity.text)/100.0)
        # manage graphic fills
    

    def isFile(self, text):
        
        try:
            fn = open(text, 'r')
            fn.close()
            return True
        except IOError:
            return False
    
    def isURL(self, text):
        if(text.startswith("http://")):
            return True
        else:
            return False
    
    

    def buildGraphic(self, symbol, graphic, loc):
        eg = ET.SubElement(graphic, "ExternalGraphic")
        onLine = ET.SubElement(eg, "OnlineResource")
        onLine.text = loc
        fmt = ET.SubElement(eg, "Format")
        filename, file_extension = os.path.splitext(loc)
        if file_extension=='.png':
            fmt.text = "image/png" # calculate this
        elif file_extension == '.gif':
            fmt.text = 'image/gif'
        elif file_extension == '.jpg':
            fmt.text = 'image/jpeg'
        elif file_extension == '.svg':
            fmt.text = 'image/svg+xml'
        else:
            fmt.text = file_extension
            
    def is_number(self,s):
        try:
            float(s) # for int, long and float
        except ValueError:
            return False
        
        return True    
        

    def getGraphic(self, style, symb):
        symbol = style.find('{http://www.mapserver.org/mapserver}symbol')
        if symbol is None:
            return
        graphic = ET.SubElement(symb, "Graphic")
        
        if self.is_number(symbol.text):
            #lookup in symbols table?
            pass
        elif self.isFile(symbol.text) or self.isURL(symbol.text):
            self.buildGraphic(symbol, graphic, symbol.text)
        else: #its text
            if symbol.text in self.symbols:
                s = self.symbols[symbol.text]
                if s.attrib['type'].upper() == 'pixmap'.upper():
                    self.buildGraphic(s, graphic,s.find('{http://www.mapserver.org/mapserver}image').text)
            else:
                # then it is a WKname
                mark = ET.SubElement(graphic,"Mark")
                wkn = ET.SubElement(mark,"WellKnownName")
                wkn.text = symbol.text
                self.getFill(symbol, mark)
                self.getStroke(symbol, mark)
        
        s_size = style.find('{http://www.mapserver.org/mapserver}size')
        if s_size is not None:
            size = ET.SubElement(graphic,"Size")
            size.text = s_size.text
        s_opacity = style.find('{http://www.mapserver.org/mapserver}opacity')
        if s_opacity is not None:
            opacity = ET.SubElement(graphic,"Opacity")
            opacity.text = str(float( s_opacity.text)/100.0)
        s_rot = style.find('{http://www.mapserver.org/mapserver}angle')
        if s_rot is not None:
            rotation = ET.SubElement(graphic,"Rotation")
            rotation.text = s_rot.text
        


    def getLabel(self, layer, sld, rule, label):
        labelitem = layer.find('{http://www.mapserver.org/mapserver}labelItem')
        text = label.find('{http://www.mapserver.org/mapserver}text')
        if text is None:
            if labelitem is None:
                return
            else:
                text = labelitem
        rule = ET.SubElement(sld, "Rule")
        sText = ET.SubElement(rule, "TextSymbolizer") #add scaledenoms here
        sLabel = ET.SubElement(sText, "Label")
        sLabel.text = text.text
        font = label.find('{http://www.mapserver.org/mapserver}font')
        if font is not None:
            sFont = ET.SubElement(sText, "Font")
            fam = ET.SubElement(sFont, "CssParameter", name="font-family")
            fam.text = font.text
            size = label.find('{http://www.mapserver.org/mapserver}size')
            if size is not None:
                siz = ET.SubElement(sFont, "CssParameter", name="font-size")
                siz.text = size.text 
        #lineplacement
        pos = label.find('{http://www.mapserver.org/mapserver}position')
        offset = label.find('{http://www.mapserver.org/mapserver}offset')
        angle = label.find('{http://www.mapserver.org/mapserver}angle')
        if pos is not None or offset is not None:
            labPlace = ET.SubElement(sText,"LabelPlacement")
            if layer.attrib['type'] == 'POINT' or layer.attrib['type'] == 'POLYGON':
                pPlace = ET.SubElement(labPlace,"PointPlacement")
                anchor = ET.SubElement(pPlace,"AnchorPoint")
                anchorX = ET.SubElement(anchor,"AnchorPointX")
                anchorY = ET.SubElement(anchor,"AnchorPointY")
                anchorX.text = "0.5"
                anchorY.text = "0.5"
                if pos is not None:
                    pp = pos.text
                else:
                    pp = 'CC'
                if pp == 'UL':
                    anchorX.text = "0.0"
                    anchorY.text = "1.0"
                elif pp=='UC':
                    anchorX.text = "0.5"
                    anchorY.text = "1.0"
                elif pp=='UR':  
                    anchorX.text = "1.0"
                    anchorY.text = "1.0"
                elif pp == 'CL':
                    anchorX.text = "0.0"
                    anchorY.text = "0.5"
                elif pp=='CC':
                    anchorX.text = "0.5"
                    anchorY.text = "0.5"
                elif pp=='CR':  
                    anchorX.text = "1.0"
                    anchorY.text = "0.5"
                elif pp == 'LL':
                    anchorX.text = "0.0"
                    anchorY.text = "0.0"
                elif pp=='LC':
                    anchorX.text = "0.5"
                    anchorY.text = "0.0"
                elif pp=='LR':  
                    anchorX.text = "1.0"
                    anchorY.text = "0.0"
                
                if offset is not None:
                    disp = ET.SubElement(pPlace,"Displacement")
                    dispx = ET.SubElement(disp,"DisplacementX")
                    dispx.text = offset.attrib['x']
                    dispy = ET.SubElement(disp,"DisplacementY")
                    dispy.text = offset.attrib['y']
                if angle is not None:
                    ang = ET.SubElement(pPlace,"Rotation")
                    ang.text = angle.text
            elif layer.attrib['type'] == 'LINE':
                if offset is not None:
                    lPlace = ET.SubElement(labPlace,"LinePlacement")
                    pOffset = ET.SubElement(lPlace,"PerpendicularOffset")
                # I'm guessing here!
                    pOffset.text = offset.attrib['y']
                
            
        #halo
        outCol = label.find('{http://www.mapserver.org/mapserver}outlineColor')
        if outCol is not None:
            halo = ET.SubElement(sText, "Halo")
            fill = ET.SubElement(halo, "Fill")
            col = ET.SubElement(fill, "CssParameter", name="fill")
            self.set_color(col, outCol)
        ccol = label.find('{http://www.mapserver.org/mapserver}color')
        if ccol is not None:
            fill = ET.SubElement(sText, "Fill")
            col = ET.SubElement(fill, "CssParameter", name="fill")
            self.set_color(col, ccol)


    def makeFilter(self, rule, classitem, expression):
        exprText = expression.text
        if exprText is None:
            filterEl = ET.SubElement(rule,"ElseFilter")
            return
        else:
            filterEl = ET.SubElement(rule, "Filter")
        if exprText.startswith('/'):
            f = ET.SubElement(filterEl,"PropertyIsLike")
            exprText = exprText.replace('/','%')
        else: 
            f = ET.SubElement(filterEl,"PropertyNameIsEqualTo")
            
        prop = ET.SubElement(f, "PropertyName" )
        prop.text = classitem.text
        literal = ET.SubElement(f,"Literal")
        literal.text = exprText
        
    def __init__(self, input_file, root=None):
        self.input = input_file
        nsmap={None:"http://www.mapserver.org/mapserver"}
        self.layers = {} 
        self.layer_info = {}
        #read in xml 
        if root is None:
            tree=ET.parse(input_file)
            root = tree.getroot()
    
        ns = root.nsmap[None]
        
        
        # for some reason the tree has no namespace on the tags when passed in 
        # directly instead of being parsed.
        # so fix it!
        for x in root.getiterator():
            if not '{' in x.tag:
                x.tag = "{"+ns+"}"+x.tag
                
            
        self.symbols = {}
        for symbol in root.iterfind(QName(ns, 'Symbol')):
            self.symbols[symbol.attrib['name']] = symbol
           
        
        layerRef = QName(ns, 'Layer')
        #print "LayerRef="+layerRef.text
        for layer in root.iterfind(layerRef): #
            layer_type =layer.attrib['type']
            layer_name = layer.attrib['name']
            class_item = layer.find('classItem')
            #print str(layer_type) +" "+str(layer_name)
            sld = ET.Element("FeatureTypeStyle")
            #,nsmap={None:"http://www.opengis.net/sld","ogc":"http://www.opengis.net/ogc"} 
            for class_ in layer.iterfind(QName(ns, 'Class')):
                rule = ET.SubElement(sld, "Rule")
                name = ET.SubElement(rule, "Name")
                if 'name' in class_.attrib and not class_.attrib['name'] == '':
                    rule.set("name",class_.attrib['name'])
                    name.text = class_.attrib['name']
                if name.text == None:
                    name.text = "."
                #filter
                classitem = layer.find(QName(ns, 'classItem'))
                if classitem is not None:
                    expression = class_.find(QName(ns, 'expression'))
                    if expression is not None:
                        
                        self.makeFilter(rule,classitem,expression)
                #scale denoms
                minscale = layer.find(QName(ns, 'minScaleDenom'))
                if minscale is not None:
                    mins = ET.SubElement(rule,"MinScaleDenominator")
                    mins.text = minscale.text
                maxscale = layer.find(QName(ns, 'maxScaleDenom'))
                if maxscale is not None:
                    maxs = ET.SubElement(rule,"MaxScaleDenominator")
                    maxs.text = maxscale.text
                
                
                for style in class_.iterfind(QName(ns, 'Style')):
                    minscale = style.find(QName(ns, 'labelMinScaleDenom'))
                    if minscale is not None:
                        mins = ET.SubElement(rule,"MinScaleDenominator")
                        mins.text = minscale.text
                    maxscale = style.find(QName(ns, 'labelMaxScaleDenom'))
                    if maxscale is not None:
                        maxs = ET.SubElement(rule,"MaxScaleDenominator")
                        maxs.text = maxscale.text
                        
                    if layer_type.upper() == 'LINE':
                        symb = ET.SubElement(rule, "LineSymbolizer")
                        self.getStroke(style, symb, isLine=True)
                            
                    elif layer_type.upper() == 'POLYGON':
                        symb = ET.SubElement(rule, "PolygonSymbolizer")
                        self.getFill(style, symb)
                        self.getStroke(style, symb)
                    elif layer_type.upper() == 'POINT':
                        symb = ET.SubElement(rule, "PointSymbolizer")
                        self.getGraphic(style,symb)
                    else:
                        print "Unknown layer type "+str(layer_type) + " for "+str(layer_name)
                        
                for label in class_.iterfind(QName(ns, 'Label')):
                    minscale = layer.find(QName(ns, 'labelMinScaleDenom'))
                    if minscale is not None:
                        mins = ET.SubElement(rule,"MinScaleDenominator")
                        mins.text = minscale.text
                    maxscale = layer.find(QName(ns, 'labelMaxScaleDenom'))
                    if maxscale is not None:
                        maxs = ET.SubElement(rule,"MaxScaleDenominator")
                        maxs.text = maxscale.text
                    self.getLabel(layer, sld, rule, label)
            #ET.dump(sld)
            self.layers[layer.attrib['name']] = sld
            self.layer_info[layer.attrib['name']] = layer               
                           
    def getLayer(self,name):
        if name in self.layers:
            return self.layers[name]
        else:
            return None
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("inputfile", type=str, help="the map file to be processed")
    #parser.add_argument("-o", "--outputfile", type=str, help="the file to write output to (stdout if missing)", default="")
    
    
    args = parser.parse_args()
    
    
    sldStore = xml_to_sld(args.inputfile)
    
    for layer in sldStore.layers:
        print layer
        ET.dump(sldStore.getLayer(layer))
    
    
    # for el in mapper.map_root:
        # print el
     

if __name__ == "__main__":
    main()        
