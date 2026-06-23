<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="text" indent="no" encoding="utf-16"/>
  <xsl:template match="/data/instruments" name="instruments">
    <xsl:for-each select="/data/instruments/instrument">
      <xsl:sort select="@number" order="ascending"/>
      <xsl:text>&#x0D;&#x0A;</xsl:text>
      <xsl:text>[PCS,</xsl:text>
      <xsl:value-of select="@number"/>
      <xsl:text>]&#x0D;&#x0A;</xsl:text>

      <xsl:text>InstType=</xsl:text>
      <xsl:choose>
        <xsl:when test="@type = 'LC'">lcoffline</xsl:when>
        <xsl:when test="@type = 'GC'">gcoffline</xsl:when>
        <xsl:when test="@type = 'CE'">ceoffline</xsl:when>
        <xsl:when test="@type = 'LCMS'">lcoffline</xsl:when>
      </xsl:choose>
      <xsl:text>&#x0D;&#x0A;</xsl:text>

      <xsl:text>InstName=</xsl:text>
      <xsl:value-of select="@name"/>
      <xsl:text>&#x0D;&#x0A;</xsl:text>
      <xsl:text>WinSize=Normal&#x0D;&#x0A;</xsl:text>
      <xsl:text>Start=No&#x0D;&#x0A;</xsl:text>
      <xsl:text>Program=</xsl:text>
      <xsl:value-of select="concat(/data/general/@installpath,'\CORE\ChemMain.exe')"/>
      <xsl:text>&#x0D;&#x0A;</xsl:text>

      <xsl:text>DEBackground=</xsl:text>
      <xsl:choose>
        <xsl:when test="@type = 'CE'">192 192 192&#x0D;&#x0A;</xsl:when>
        <xsl:otherwise>255 255 255&#x0D;&#x0A;</xsl:otherwise>
      </xsl:choose>

      <xsl:text>DEChromatogram=255 255 255&#x0D;&#x0A;</xsl:text>
      <xsl:text>DEAxes=000 000 000&#x0D;&#x0A;</xsl:text>
      <xsl:text>DERtimes=000 000 000&#x0D;&#x0A;</xsl:text>
      <xsl:text>DEBaselines=255 000 255&#x0D;&#x0A;</xsl:text>
      <xsl:text>DEChrom1=000 000 255&#x0D;&#x0A;</xsl:text>
      <xsl:text>DEChrom2=255 000 000&#x0D;&#x0A;</xsl:text>
      <xsl:text>DEChrom3=000 128 000&#x0D;&#x0A;</xsl:text>
      <xsl:text>DEAnnotation=000 000 000&#x0D;&#x0A;</xsl:text>
      <xsl:text>DEFrame=255 000 000&#x0D;&#x0A;</xsl:text>
      <xsl:text>DETitle=255 0 255&#x0D;&#x0A;</xsl:text>
      <xsl:text>DEAxesTitle=0 0 0&#x0D;&#x0A;</xsl:text>
      <xsl:text>DECompounds=255 0 255&#x0D;&#x0A;</xsl:text>
      <xsl:text>DEChrom4=255 000 255&#x0D;&#x0A;</xsl:text>
      <xsl:text>DEChrom5=128 128 0&#x0D;&#x0A;</xsl:text>
      <xsl:text>DEChrom6=128 0 128&#x0D;&#x0A;</xsl:text>
      <xsl:text>DEChrom7=0 64 0&#x0D;&#x0A;</xsl:text>
      <xsl:text>DEChrom8=64 128 128&#x0D;&#x0A;</xsl:text>

      <xsl:text>_AUTOPATH$=</xsl:text>
      <xsl:value-of select="concat(/data/general/@installpath, '\CORE\&#x0D;&#x0A;')"/>
      <xsl:text>_EXEPATH$=</xsl:text>
      <xsl:value-of select="concat(/data/general/@installpath, '\CORE\&#x0D;&#x0A;')"/>
      <xsl:text>_INSTPATH$=</xsl:text>
      <xsl:value-of select="concat(/data/general/@installpath, '\', @number, '\&#x0D;&#x0A;')"/>
      <xsl:text>_DATAPATH$=</xsl:text>
      <xsl:value-of select="concat(/data/general/@installpath, '\', @number, '\DATA\&#x0D;&#x0A;')"/>
      <xsl:text>_DATAFILE$=DEFAULT.D&#x0D;&#x0A;</xsl:text>

      <xsl:text>_METHFILE$=</xsl:text>
      <xsl:choose>
        <xsl:when test="@type = 'LC'">DEF_LC.M</xsl:when>
        <xsl:when test="@type = 'GC'">DEF_GC.M</xsl:when>
        <xsl:when test="@type = 'CE'">DEF_CE.M</xsl:when>
        <xsl:when test="@type = 'LCMS'">DEF_LC.M</xsl:when>
      </xsl:choose>
      <xsl:text>&#x0D;&#x0A;</xsl:text>

      <xsl:text>_CONFIGSEQPATH$=</xsl:text>
      <xsl:value-of select="concat(/data/general/@installpath, '\', @number, '\SEQUENCE\&#x0D;&#x0A;')"/>
      <xsl:text>_CONFIGMETPATH$=</xsl:text>
      <xsl:value-of select="concat(/data/general/@installpath, '\', @number, '\METHODS\')"/>
      <xsl:if test="@type = 'CE'">CE\</xsl:if>
      <xsl:text>&#x0D;&#x0A;</xsl:text>

      <xsl:text>_SEQFILE$=</xsl:text>
      <xsl:choose>
        <xsl:when test="@type = 'LC'">DEF_LC.S</xsl:when>
        <xsl:when test="@type = 'GC'">DEF_GC.S</xsl:when>
        <xsl:when test="@type = 'CE'">DEF_CE.S</xsl:when>
        <xsl:when test="@type = 'LCMS'">DEF_LC.S</xsl:when>
      </xsl:choose>
      <xsl:text>&#x0D;&#x0A;</xsl:text>

      <xsl:text>ProductNumbers=</xsl:text>
      <xsl:value-of select="@ProductNumbers"/>
      <xsl:text>&#x0D;&#x0A;</xsl:text>


      <xsl:text>_PRODUCT$=</xsl:text>
      <xsl:choose>
        <xsl:when test="@type = 'LC' and @spectra = 'true'">DA-LC3D-LC</xsl:when>
        <xsl:when test="@type = 'LC' and @spectra = 'false'">DA-LC-LC</xsl:when>
        <xsl:when test="@type = 'GC'">DA-GC-GC</xsl:when>
        <xsl:when test="@type = 'CE' and @msAddon = 'true'">DA-CEMS-CE</xsl:when>
        <xsl:when test="@type = 'CE' and @msAddon = 'false'">DA-CE-CE</xsl:when>
        <xsl:when test="@type = 'LCMS'">DA-LCMS-LC</xsl:when>
      </xsl:choose>
      <xsl:text>&#x0D;&#x0A;</xsl:text>

      <xsl:choose>
        <xsl:when test="@type = 'GC'">
          <xsl:text>ADDONS=1&#x0D;&#x0A;</xsl:text>
          <xsl:text>ADDON1=</xsl:text>
          <xsl:value-of select="concat(/data/general/@installpath, '\GC\RTLTOP.MAC&#x0D;&#x0A;')"/>
        </xsl:when>

        <!-- <xsl:when test="@type = 'CE' and @msAddon = 'false' and @daOnly = 'false'">
          <xsl:text>Devices=1,2&#x0D;&#x0A;</xsl:text>
        </xsl:when>
        -->
        <xsl:when test="@type ='CE' and @msAddon = 'true' and @daOnly = 'false'">
          <!-- 
          <xsl:text>Devices=1,2&#x0D;&#x0A;</xsl:text>
          -->
          <xsl:text>ADDONS=1&#x0D;&#x0A;</xsl:text>
          <xsl:text>ADDON1=</xsl:text>
          <xsl:value-of select="concat(/data/general/@installpath, '\MS\MSTOP.MAC&#x0D;&#x0A;')"/>
        </xsl:when>
        
        <xsl:when test="@type = 'LCMS'">
          <xsl:text>ADDONS=1&#x0D;&#x0A;</xsl:text>
          <xsl:text>ADDON1=</xsl:text>
          <xsl:value-of select="concat(/data/general/@installpath, '\MS\MSTOP.MAC&#x0D;&#x0A;')"/>
        </xsl:when>
      </xsl:choose>

    </xsl:for-each>
  </xsl:template>
</xsl:stylesheet>