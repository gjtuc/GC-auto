<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:fn="http://www.w3.org/2005/xpath-functions">

  <xsl:include href = "Automation2CSReader.xslt"/>

  <xsl:variable name="FrontInjector">front</xsl:variable>
  <xsl:variable name="BackInjector">back</xsl:variable>
  <xsl:variable name="FrontInjectorAttr">FRONT</xsl:variable>
  <xsl:variable name="BackInjectorAttr">BACK</xsl:variable>

  <xsl:output omit-xml-declaration="no" method="xml" version="1.0" encoding="utf-16" indent="yes"/>

  <xsl:template match="/">
    <xsl:apply-templates select="/AutomationEngineSequence" />
  </xsl:template>

  <xsl:template match="/AutomationEngineSequence">
    <xsl:element name="Sequence">
      <xsl:call-template name="ReadSequenceTable">
        <xsl:with-param name="SourceInjector" select="$FrontInjector"/>
        <xsl:with-param name="SourceInjectorAttr" select="$FrontInjectorAttr"/>
      </xsl:call-template>
      <xsl:call-template name="ReadSequenceTable">
        <xsl:with-param name="SourceInjector" select="$BackInjector"/>
        <xsl:with-param name="SourceInjectorAttr" select="$BackInjectorAttr"/>
      </xsl:call-template>
    </xsl:element>
  </xsl:template>

  <xsl:template name="ReadSequenceTable">
    <xsl:param name="SourceInjector"/>
    <xsl:param name="SourceInjectorAttr"/>
    <xsl:element name="Samples">
      <xsl:attribute name="Injector">
        <xsl:value-of select="$SourceInjectorAttr"/>
      </xsl:attribute>
      <xsl:call-template name="ReadBracketedCalibration">
        <xsl:with-param name="SourceInjector" select="$SourceInjector"/>
      </xsl:call-template>
      <xsl:apply-templates select="UnrolledSequence">
        <xsl:with-param name="SourceInjector" select="$SourceInjector"/>
      </xsl:apply-templates>
    </xsl:element>
  </xsl:template>

  <xsl:template name="ReadBracketedCalibration" match="BracketedCalibrationSpecification">
    <xsl:param name="SourceInjector"/>
    <xsl:variable name="ActiveInjectors">
      <xsl:value-of select="/AutomationEngineSequence/SequenceGeneration/ActiveInjectors" />
    </xsl:variable>
    <xsl:for-each select="BracketedCalibrationSpecification/BracketedCalibration">
      <xsl:if test="($SourceInjector='front') and (($ActiveInjectors=1) or ($ActiveInjectors=3)) or ($SourceInjector='back') and (($ActiveInjectors=2) or ($ActiveInjectors=3)) ">
        <xsl:element name="Sample">
          <xsl:element name="Number">
            <xsl:number count="BracketedCalibration"/>
          </xsl:element>
          <xsl:variable name="NumberOfInjections">
            <xsl:call-template name="ReadBracketInjectionsPerVial" />
          </xsl:variable>
          <xsl:variable name="Interval">
            <xsl:call-template name="ReadBracketInterval" />
          </xsl:variable>
          <xsl:apply-templates select="Sample">
            <xsl:with-param name="NumberOfInjections" select="$NumberOfInjections"/>
            <xsl:with-param name="Interval" select="$Interval"/>
          </xsl:apply-templates>
        </xsl:element>
      </xsl:if>
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="ReadSequenceTableBody" match="UnrolledSequence">
    <xsl:param name="SourceInjector"/>
    <xsl:for-each select="AnalyticalRun">
      <xsl:for-each select="Sample">
        <xsl:if test="@Source=$SourceInjector">
          <xsl:element name="Sample">
            <xsl:element name="Number">
              <xsl:number count="AnalyticalRun"/>
            </xsl:element>
            <xsl:variable name="NumberOfInjections">
              <xsl:call-template name="ReadNumberOfInj" />
            </xsl:variable>
            <xsl:variable name="Interval">
              <xsl:call-template name="ReadInterval" />
            </xsl:variable>
            <xsl:call-template name="ReadSample">
              <xsl:with-param name="NumberOfInjections" select="$NumberOfInjections"/>
              <xsl:with-param name="Interval" select="$Interval"/>
            </xsl:call-template>
          </xsl:element>
        </xsl:if>
      </xsl:for-each>
    </xsl:for-each>
  </xsl:template>

  <!--format a sequence line-->
  <xsl:template name="ReadSample" match="Sample">
    <xsl:param name="NumberOfInjections"/>
    <xsl:param name="Interval"/>
    <xsl:element name="Location">
      <xsl:call-template name="ReadLocation" />
    </xsl:element>
    <xsl:element name="Name">
      <xsl:call-template name="ReadName" />
    </xsl:element>
    <xsl:element name="CDSMethod">
      <xsl:call-template name="ReadCDSMethod" />
    </xsl:element>
    <xsl:element name="numberOfInj">
      <xsl:value-of select="$NumberOfInjections" />
    </xsl:element>
    <xsl:element name="sampleType">
      <xsl:call-template name="ReadSampleType" />
    </xsl:element>
    <xsl:element name="CalLevel">
      <xsl:call-template name="ReadCalLevel" />
    </xsl:element>
    <xsl:element name="calibration">
      <xsl:call-template name="ReadCalibration"/>
    </xsl:element>
    <xsl:element name="UpdateRT">
      <xsl:call-template name="ReadUpdateRT" />
    </xsl:element>
    <xsl:element name="Interval">
      <xsl:value-of select="$Interval" />
    </xsl:element>
    <xsl:element name="sampleAmount">
      <xsl:call-template name="ReadSampleAmount" />
    </xsl:element>
    <xsl:element name="ISTDAmount">
      <xsl:call-template name="ReadISTDAmount" />
    </xsl:element>
    <xsl:element name="Multipliers">
      <xsl:call-template name="ReadMultipliers" />
    </xsl:element>
    <xsl:element name="Dilution">
      <xsl:call-template name="ReadDilution" />
    </xsl:element>
    <xsl:element name="DataFilename">
      <xsl:call-template name="ReadDataFilename" />
    </xsl:element>
    <xsl:element name="InjectionVolume">
      <xsl:call-template name="ReadInjectionVolume" />
    </xsl:element>
    <xsl:element name="description">
      <xsl:call-template name="ReadDescription" />
    </xsl:element>
    <xsl:element name="StudyName">
      <xsl:call-template name="ReadStudyName" />
    </xsl:element>
    <xsl:element name="LimsID">
      <xsl:call-template name="ReadLimsID" />
    </xsl:element>
    <xsl:element name="LimsKField2">
    </xsl:element>
    <xsl:call-template name="ReadLimsKField2" />
    <xsl:element name="LimsKField3">
      <xsl:call-template name="ReadLimsKField3" />
    </xsl:element>
    <xsl:element name="AutoBalance">
      <xsl:call-template name="ReadAutoBalance" />
    </xsl:element>
    <xsl:element name="TargetMassCol">
      <xsl:call-template name="ReadTargetMasses" />
    </xsl:element>
  </xsl:template>

</xsl:stylesheet>
