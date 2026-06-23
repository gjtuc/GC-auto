<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:fn="http://www.w3.org/2005/xpath-functions">
  
  <xsl:template name="ReadLocation">
    <xsl:value-of select="Location" />
  </xsl:template>

  <xsl:template name="ReadDataLocation">
    <xsl:value-of select="DataLocation" />
  </xsl:template>

  <xsl:template name="ReadName">
    <xsl:value-of select="Name" />
  </xsl:template>

  <xsl:template name="ReadCDSMethod">
    <xsl:value-of select="AcquisitionMethod" />
  </xsl:template>

  <xsl:template name="ReadNumberOfInj">
    <xsl:choose>
      <xsl:when test="noIdea != ''">
        <xsl:value-of select="noIdea" />
      </xsl:when>
      <xsl:otherwise>1</xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="ReadSampleType">
    <xsl:choose>
      <xsl:when test="SampleType='Sample'">SAMPLE</xsl:when>
      <xsl:when test="SampleType='ControlSample'">CONTROLSAMPLE</xsl:when>
      <xsl:when test="SampleType='Calibration'">CALIBRATION</xsl:when>
      <xsl:when test="SampleType='Unknown'">UNKNOWN</xsl:when>
      <xsl:when test="SampleType='Standard'">STANDARD</xsl:when>
      <xsl:when test="SampleType='QualityControl'">QUALITYCONTROL</xsl:when>
      <xsl:when test="SampleType='Blank'">BLANK</xsl:when>
      <xsl:when test="SampleType='DoubleBlank'">DOUBLEBLANK</xsl:when>
      <xsl:when test="SampleType='Solvent'">SOLVENT</xsl:when>
      <xsl:otherwise>SAMPLE</xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="ReadCalLevel">
    <xsl:choose>
      <xsl:when test="CalibrationLevel != ''">
        <xsl:value-of select="CalibrationLevel" />
      </xsl:when>
      <xsl:otherwise>1</xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
  <xsl:template name="ReadCalibration">
    <xsl:choose>
      <xsl:when test="CalibrationUpdateResponseFactor='NoUpdate'">NO UPDATE</xsl:when>
      <xsl:when test="CalibrationUpdateResponseFactor='Replace'">REPLACE</xsl:when>
      <xsl:when test="CalibrationUpdateResponseFactor='Bracket'">BRACKET</xsl:when>
      <xsl:when test="CalibrationUpdateResponseFactor='DeltaPercent'">DELTA%</xsl:when>
      <xsl:when test="CalibrationUpdateResponseFactor='Average'">AVERAGE</xsl:when>
      <xsl:otherwise>NO UPDATE</xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="ReadUpdateRT">
    <xsl:choose>
      <xsl:when test="CalibrationUpdateRetentionTime='NoUpdate'">NO UPDATE</xsl:when>
      <xsl:when test="CalibrationUpdateRetentionTime='Replace'">REPLACE</xsl:when>
      <xsl:when test="CalibrationUpdateRetentionTime='Bracket'">BRACKET</xsl:when>
      <xsl:when test="CalibrationUpdateRetentionTime='DeltaPercent'">DELTA%</xsl:when>
      <xsl:when test="CalibrationUpdateRetentionTime='Average'">AVERAGE</xsl:when>
      <xsl:otherwise>NO UPDATE</xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="ReadBracketInjectionsPerVial">
    <xsl:value-of select="InjectionsPerVial" />
  </xsl:template>

  <xsl:template name="ReadBracketInterval">
    <xsl:value-of select="Interval" />
  </xsl:template>

  <xsl:template name="ReadInterval">
    <xsl:choose>
      <xsl:when test="noIdea != ''">
        <xsl:value-of select="noIdea" />
      </xsl:when>
      <xsl:otherwise>0</xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="ReadSampleAmount">
    <xsl:value-of select="SampleAmount[1]" />
  </xsl:template>

  <xsl:template name="ReadISTDAmount">
    <xsl:value-of select="ISTDAmount[1]" />
  </xsl:template>

  <xsl:template name="ReadMultipliers">
    <xsl:value-of select="Multiplier[1]" />
  </xsl:template>

  <xsl:template name="ReadDilution">
    <xsl:value-of select="Dilution[1]" />
  </xsl:template>

  <xsl:template name="ReadDataFilename">
    <xsl:value-of select="DataFileName" />
  </xsl:template>

  <xsl:template name="ReadInjectionVolume">
      <xsl:if test="InjectionVolume/attribute::asMethod='false'">
          <xsl:value-of select="InjectionVolume"/>
      </xsl:if>
  </xsl:template>

  <xsl:template name="ReadDescription">
    <xsl:value-of select="Description" />
  </xsl:template>

  <xsl:template name="ReadStudyName">
    <xsl:value-of select="StudyName" />
  </xsl:template>

  <xsl:template name="ReadLimsID">
    <xsl:value-of select="LimsId" />
  </xsl:template>

  <xsl:template name="ReadLimsKField2">
    <xsl:value-of select="noIdea" />
  </xsl:template>

  <xsl:template name="ReadLimsKField3">
    <xsl:value-of select="noIdea" />
  </xsl:template>

  <xsl:template name="ReadAutoBalance">
    <xsl:choose>
      <xsl:when test="AutoBalance != ''">
        <xsl:value-of select="AutoBalance" />
      </xsl:when>
      <xsl:otherwise>true</xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="ReadTargetMasses">
    <xsl:value-of select="TargetMasses" />
  </xsl:template>

</xsl:stylesheet>
