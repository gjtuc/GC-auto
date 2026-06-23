<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="text" indent="no" encoding="utf-16"/>
  <xsl:include href="Instruments.xslt"/>
  <xsl:include href="LanguageSection.xslt"/>
  <xsl:template match="/">
    <xsl:text>[CHEMSM]&#x0D;&#x0A;</xsl:text>
    <xsl:text>NUM_SIZE_32=15288&#x0D;&#x0A;</xsl:text>
    <xsl:text>NUM_SIZE_64=4072&#x0D;&#x0A;</xsl:text>
    <xsl:text>NUM_SIZE_128=3536&#x0D;&#x0A;</xsl:text>
    <xsl:text>NUM_SIZE_256=148&#x0D;&#x0A;</xsl:text>
    <xsl:text>NUM_SIZE_512=684&#x0D;&#x0A;</xsl:text>
    <xsl:text>NUM_SIZE_1024=2536&#x0D;&#x0A;</xsl:text>
    <xsl:text>NUM_SIZE_2048=392&#x0D;&#x0A;</xsl:text>
    <xsl:text>NUM_SIZE_4096=72&#x0D;&#x0A;</xsl:text>
    <xsl:text>NUM_SIZE_8192=96&#x0D;&#x0A;</xsl:text>
    <xsl:text>&#x0D;&#x0A;</xsl:text>

    <xsl:call-template name="LanguageSection"/>

    <xsl:text>[PCS]&#x0D;&#x0A;</xsl:text>
    <xsl:text>UIFont1=Arial&#x0D;&#x0A;</xsl:text>
    <xsl:text>UIFont2=MS Sans Serif&#x0D;&#x0A;</xsl:text>
    <xsl:text>UIFont3=Tahoma&#x0D;&#x0A;</xsl:text>
    <xsl:text>UIFont4=Courier New&#x0D;&#x0A;</xsl:text>
    <xsl:text>UIFont5=Courier&#x0D;&#x0A;</xsl:text>
    <xsl:text>ReportFontName=Courier New&#x0D;&#x0A;</xsl:text>
    <xsl:text>ReportFontSize=10&#x0D;&#x0A;</xsl:text>
    <xsl:text>pdf_ReportFontName=Consolas&#x0D;&#x0A;</xsl:text>
    <xsl:text>pdf_ReportFontSize=10&#x0D;&#x0A;</xsl:text>
    <xsl:text>pdf_ReportFontWeight=700&#x0D;&#x0A;</xsl:text>
    <xsl:text>Pdf_viewer_NO_XLS=1&#x0D;&#x0A;</xsl:text>
    <xsl:text>Pdf_viewer_MRC_view=0&#x0D;&#x0A;</xsl:text>
    <xsl:text>Path=</xsl:text> <xsl:value-of select="data/general/@installpath"/> <xsl:text>&#x0D;&#x0A;</xsl:text>
    <xsl:text>WIN2K=1&#x0D;&#x0A;</xsl:text>
    <xsl:text>Links=1&#x0D;&#x0A;</xsl:text>
    <xsl:text>Link1=HPBSICL,1,15,0,3&#x0D;&#x0A;</xsl:text>
    <xsl:text>UsePoll=Yes&#x0D;&#x0A;</xsl:text>

    <xsl:text>Applications=</xsl:text>
    <xsl:for-each select="data/instruments/instrument">
      <xsl:sort select="@number" order="ascending"/>
      <xsl:choose>
        <xsl:when test="@type = 'LC'">HP-LC</xsl:when>
        <xsl:when test="@type = 'GC'">HPGC</xsl:when>
        <xsl:when test="@type = 'CE'">HPCE</xsl:when>
        <xsl:when test="@type = 'LCMS'">HP-LC</xsl:when>
        <xsl:otherwise>unknown instrument type</xsl:otherwise>
      </xsl:choose>
      <xsl:if test="count(//instrument) &gt; @number">,</xsl:if>
    </xsl:for-each>
    <xsl:text>&#x0D;&#x0A;</xsl:text>  

    <xsl:text>Instruments=</xsl:text>
    <xsl:for-each select="data/instruments/instrument">
      <xsl:sort select="@number" order="ascending"/>
      <xsl:value-of select="@number"/>
      <xsl:if test="count(//instrument) &gt; @number">,</xsl:if>
    </xsl:for-each>
    <xsl:text>&#x0D;&#x0A;</xsl:text>

    <xsl:text>ProductNumbers=</xsl:text><xsl:value-of select="data/general/@ProductNumbers"/><xsl:text>&#x0D;&#x0A;</xsl:text>
    <xsl:text>REV=</xsl:text><xsl:value-of select="data/general/@revision"/><xsl:text>&#x0D;&#x0A;</xsl:text>
    <xsl:text>BASEREV=</xsl:text><xsl:value-of select="data/general/@baserevision"/><xsl:text>&#x0D;&#x0A;</xsl:text>
    <xsl:if test="//instrument/@type = 'CE' and //instrument/@daOnly = 'false'">
      <xsl:text>Device1=1,19,HPCE&#x0D;&#x0A;</xsl:text>
      <xsl:text>Devices=1,2&#x0D;&#x0A;</xsl:text>
      <xsl:text>Device2=1,17,79854C&#x0D;&#x0A;</xsl:text>
    </xsl:if>
    <xsl:if test="//instrument/@type = 'LC' or //instrument/@type = 'LCMS'">
      <xsl:text>PumpUseBar=1&#x0D;&#x0A;</xsl:text>  
    </xsl:if>
    <xsl:text>&#x0D;&#x0A;</xsl:text>
    <xsl:text>;macdebug=1&#x0D;&#x0A;</xsl:text>
    <xsl:text>;macdebugpath=c:\mac_dbg32&#x0D;&#x0A;</xsl:text>
    <xsl:text>&#x0D;&#x0A;</xsl:text>
    <xsl:call-template name="instruments"/>
    
  </xsl:template>
  

</xsl:stylesheet>