<?xml version="1.0" encoding="UTF-8"?>
<!-- edited with XMLSPY v5 rel. 2 U (http://www.xmlspy.com) by Reiner Lange (Agilent Technologies) -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="text" omit-xml-declaration="yes" encoding="iso-8859-1"/>
	<xsl:template match="/">
		<xsl:for-each select="Samples/Sample">Number&#9; <xsl:value-of select="Number"/> &#9;Vial&#9; <xsl:value-of select="Location"/> &#9;SampleName&#9; <xsl:value-of select="Name"/>&#9;Method&#9; <xsl:value-of select="CDSMethod"/> &#9;InjVial&#9; <xsl:value-of select="numberOfInj"/>&#9;SampleType&#9; <xsl:value-of select="sampleType"/>&#9;SampleInfo&#9; <xsl:value-of select="description"/>&#9;CalLevel&#9; <xsl:value-of select="CalLevel"/>&#9;UpdateRF&#9; <xsl:value-of select="calibration"/>&#9;UpdateRT&#9; <xsl:value-of select="UpdateRT"/> &#9;Interval&#9; <xsl:value-of select="Interval"/>&#9;Amount&#9; <xsl:value-of select="sampleAmount"/>&#9;ISTDAmt&#9; <xsl:value-of select="ISTDAmount"/>&#9;Multiplier&#9; <xsl:value-of select="Multipliers"/>&#9;Dilution&#9; <xsl:value-of select="Dilution"/>&#9;DataFilename&#9; <xsl:value-of select="DataFilename"/>&#9;InjVolume&#9; <xsl:value-of select="InjectionVolume"/>&#9;StudyName&#9; <xsl:value-of select="StudyName"/>&#9;LimsKField1&#9; <xsl:value-of select="LimsID"/>&#9;LimsKField2&#9; <xsl:value-of select="LimsKField2"/>&#9;LimsKField3&#9; <xsl:value-of select="LimsKField3"/>			<xsl:for-each select="CustomField">
&#9; <xsl:value-of select="Name"/>&#9; <xsl:value-of select="Value"/>
</xsl:for-each>&#9;<xsl:text>&#xd;&#xa;</xsl:text> 
</xsl:for-each>
</xsl:template>
</xsl:stylesheet>
