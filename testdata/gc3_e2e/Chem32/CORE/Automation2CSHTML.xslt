<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:fn="http://www.w3.org/2005/xpath-functions">

  <xsl:include href = "Automation2CSReader.xslt"/>

  <xsl:variable name="FrontInjector">front</xsl:variable>
  <xsl:variable name="BackInjector">back</xsl:variable>

  <xsl:template match="/">
    <html>
      <body>
        <xsl:apply-templates select="/AutomationEngineSequence/SequenceGeneration" />
        <P>Data Location: <xsl:apply-templates select="/AutomationEngineSequence/DataLocation" /></P>
        <xsl:apply-templates select="/AutomationEngineSequence" />
      </body>
    </html>
  </xsl:template>
  
  <xsl:template match="/AutomationEngineSequence/SequenceGeneration">
    <h2>Sample Set Name: <xsl:value-of select="SampleSetName" /></h2>
    <P>Template: <xsl:value-of select="TemplateLocator" /></P>
    <P>Generated: <xsl:value-of select="Generated" /></P>
  </xsl:template>

  <xsl:template match="/AutomationEngineSequence">
    <xsl:call-template name="ReadSequenceTable">
      <xsl:with-param name="SourceInjector" select="$FrontInjector"/>
    </xsl:call-template>
    <xsl:call-template name="ReadSequenceTable">
      <xsl:with-param name="SourceInjector" select="$BackInjector"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="ReadSequenceTable">
    <xsl:param name="SourceInjector"/>
    <h3>
      <xsl:value-of select="$SourceInjector" />
    </h3>
    <table border="1">
      <tr bgcolor="#9acd32">
        <th>Number</th>
        <th>numberOfInj</th>
        <th>Interval</th>
        <th>Location</th>
        <th>Name</th>
        <th>CDSMethod</th>
        <th>sampleType</th>
        <th>calLevel</th>
        <th>Calibration</th>
        <th>UpdateRT</th>
        <th>sampleAmount</th>
        <th>ISTDAmount</th>
        <th>Multipliers</th>
        <th>Dilution</th>
        <th>DataFilename</th>
        <th>InjectionVolume</th>
        <th>description</th>
        <th>StudyName</th>
        <th>LimsID</th>
        <th>LimsKField2</th>
        <th>LimsKField3</th>
        <th>AutoBalance</th>
        <th>TargetMasses</th>
      </tr>
      <xsl:call-template name="ReadBracketedCalibration">
        <xsl:with-param name="SourceInjector" select="$SourceInjector"/>
      </xsl:call-template>
      <xsl:apply-templates select="UnrolledSequence">
        <xsl:with-param name="SourceInjector" select="$SourceInjector"/>
      </xsl:apply-templates>
    </table>
  </xsl:template>

  <xsl:template name="ReadBracketedCalibration" match="BracketedCalibrationSpecification">
    <xsl:param name="SourceInjector"/>
    <xsl:variable name="ActiveInjectors">
      <xsl:value-of select="/AutomationEngineSequence/SequenceGeneration/ActiveInjectors" />
    </xsl:variable>
    <xsl:for-each select="BracketedCalibrationSpecification/BracketedCalibration">
      <xsl:if test="($SourceInjector='front') and (($ActiveInjectors=1) or ($ActiveInjectors=3)) or ($SourceInjector='back') and (($ActiveInjectors=2) or ($ActiveInjectors=3)) ">
        <tr>
        <td><xsl:number count="BracketedCalibration"/></td>
        <td><xsl:call-template name="ReadBracketInjectionsPerVial" /></td>
        <td><xsl:call-template name="ReadBracketInterval" /></td>
        <xsl:apply-templates select="Sample" />
      </tr>
      </xsl:if>
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="ReadSequenceTableBody" match="UnrolledSequence">
     <xsl:param name="SourceInjector"/>
     <xsl:for-each select="AnalyticalRun">
       <xsl:for-each select="Sample">
         <xsl:if test="@Source=$SourceInjector">
             <tr>
             <td><xsl:number count="AnalyticalRun"/></td>
             <td><xsl:call-template name="ReadNumberOfInj" /></td>
             <td><xsl:call-template name="ReadInterval" /></td>
             <xsl:call-template name="ReadSample" />
             </tr>
         </xsl:if>
       </xsl:for-each>
     </xsl:for-each>
  </xsl:template>

  <xsl:template match="Interval">
  </xsl:template>

  <!--format a sequence line-->
  <xsl:template name="ReadSample"  match="Sample">
        <td><xsl:call-template name="ReadLocation" /></td>
        <td><xsl:call-template name="ReadName" /></td>
        <td><xsl:call-template name="ReadCDSMethod" /></td>
        <td><xsl:call-template name="ReadSampleType" /></td>
        <td><xsl:call-template name="ReadCalLevel" /></td>
        <td><xsl:call-template name="ReadCalibration"/></td>
        <td><xsl:call-template name="ReadUpdateRT" /></td>
        <td><xsl:call-template name="ReadSampleAmount" /></td>
        <td><xsl:call-template name="ReadISTDAmount" /></td>
        <td><xsl:call-template name="ReadMultipliers" /></td>
        <td><xsl:call-template name="ReadDilution" /></td>
        <td><xsl:call-template name="ReadDataFilename" /></td>
        <td><xsl:call-template name="ReadInjectionVolume" /></td>
        <td><xsl:call-template name="ReadDescription" /></td>
        <td><xsl:call-template name="ReadStudyName" /></td>
        <td><xsl:call-template name="ReadLimsID" /></td>
        <td><xsl:call-template name="ReadLimsKField2" /></td>
        <td><xsl:call-template name="ReadLimsKField3" /></td>
        <td><xsl:call-template name="ReadAutoBalance" /></td>
        <td><xsl:call-template name="ReadTargetMasses" /></td>
  </xsl:template>

</xsl:stylesheet>
