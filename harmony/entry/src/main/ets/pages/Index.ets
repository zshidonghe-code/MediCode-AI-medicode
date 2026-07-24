import { AuthGateway } from '../service/AuthGateway';
import { ReviewDocument, ReviewSnapshot } from '../model/ReviewModels';
import { ContinuationState } from '../service/ContinuationState';
import { LocalPrivacyGate } from '../service/LocalPrivacyGate';
import { ReviewGateway } from '../service/ReviewGateway';

const LEFT_FRACTURE = '\u5de6\u4fa7\u5168\u9acb\u5173\u8282\u7f6e\u6362\u672f\u540e\u5165\u9662\u590d\u67e5\uff0c\u5207\u53e3\u60c5\u51b5\u7a33\u5b9a\u3002';
const RIGHT_SURGERY = '\u53f3\u4fa7\u5168\u9acb\u5173\u8282\u7f6e\u6362\u672f\u5df2\u5b8c\u6210\uff0c\u672f\u540e\u751f\u547d\u4f53\u5f81\u5e73\u7a33\u3002';

@Entry
@Component
struct Index {
  @State endpoint: string = 'http://127.0.0.1:8000';
  @State username: string = 'coder';
  @State password: string = '';
  @State token: string = '';
  @State authenticated: boolean = false;
  @State admissionText: string = LEFT_FRACTURE;
  @State surgeryText: string = RIGHT_SURGERY;
  @State task: ReviewSnapshot | undefined = undefined;
  @State message: string = '\u5c1a\u672a\u521b\u5efa\u5ba1\u6838\u4efb\u52a1';
  @State privacySummary: string = '';
  @State timeline: string = '';
  @State reportVisible: boolean = false;
  @State reportStatus: string = '';
  @State reportMode: string = '';
  @State reportQualityScore: string = '--';
  @State reportIssueCount: string = '0';
  @State reportCriticalCount: string = '0';
  @State reportMajorCount: string = '0';
  @State reportPrimaryDiagnosis: string = '\u672a\u751f\u6210';
  @State reportProcedure: string = '\u65e0';
  @State reportEvidence: string = '\u672a\u53d1\u73b0\u8de8\u6587\u4e66\u8bc1\u636e\u51b2\u7a81\u3002';
  @State reportDecision: string = '\u6682\u65e0\u4eba\u5de5\u51b3\u7b56\u3002';
  @State reportRedaction: string = '\u672c\u5730\u8131\u654f\u5df2\u5904\u7406 0 \u9879\u3002';
  @State reportIssues: string = '\u6682\u65e0\u8d28\u63a7\u95ee\u9898\u3002';
  @State busy: boolean = false;

  build() {
    Scroll() {
      Column({ space: 14 }) {
        this.header()
        this.connectionPanel()
        this.documentPanel()
        this.taskPanel()
        this.reportPanel()
        this.timelinePanel()
      }
      .width('100%')
      .padding({ left: 16, right: 16, top: 20, bottom: 32 })
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F6F8FA')
  }

  @Builder
  header() {
    Column({ space: 6 }) {
      Text('\u7801\u533b\u5ba1\u6838\u667a\u80fd\u4f53')
        .fontSize(24)
        .fontWeight(FontWeight.Bold)
        .fontColor('#152238')
      Text('\u672c\u5730\u8131\u654f  |  \u8bc1\u636e\u590d\u6838  |  \u4eba\u5de5\u786e\u8ba4  |  \u53ef\u8ffd\u6eaf\u62a5\u544a')
        .fontSize(14)
        .fontColor('#5B6B7F')
    }
    .alignItems(HorizontalAlign.Start)
    .width('100%')
  }

  @Builder
  connectionPanel() {
    Column({ space: 8 }) {
      Text('\u79c1\u6709\u5316\u8fde\u63a5').fontSize(16).fontWeight(FontWeight.Medium)
      TextInput({ text: this.endpoint, placeholder: 'http://intranet-host:8000' })
        .onChange((value: string) => this.changeEndpoint(value))
        .width('100%')
      TextInput({ text: this.username, placeholder: '\u8fd0\u8425\u8d26\u53f7' })
        .onChange((value: string) => this.username = value)
        .width('100%')
      TextInput({ text: this.password, placeholder: '\u8fd0\u8425\u5458\u5bc6\u7801' })
        .type(InputType.Password)
        .onChange((value: string) => this.password = value)
        .width('100%')
      Button(this.authenticated ? '\u5df2\u8fde\u63a5' : '\u767b\u5f55\u5185\u7f51')
        .enabled(!this.busy && !this.authenticated)
        .onClick(() => this.login())
        .width('100%').backgroundColor('#176B87')
      if (this.authenticated) {
        Text(`\u5df2\u767b\u5f55\uff1a${this.username}`).fontSize(13).fontColor('#19715C')
      }
    }
    .alignItems(HorizontalAlign.Start)
    .width('100%')
    .padding(14)
    .backgroundColor(Color.White)
    .borderRadius(6)
  }

  @Builder
  documentPanel() {
    Column({ space: 8 }) {
      Text('\u75c5\u5386\u4efb\u52a1\u8f93\u5165').fontSize(16).fontWeight(FontWeight.Medium)
      Text('\u5f55\u5165\u6216\u7cfb\u7edf\u5206\u4eab\u7684\u6587\u4e66\u4f1a\u5148\u5728\u672c\u5730\u8131\u654f\uff0c\u518d\u53d1\u5f80\u533b\u9662\u5185\u7f51\u3002')
        .fontSize(13).fontColor('#5B6B7F')
      Text('\u5165\u9662\u8bb0\u5f55').fontSize(13).fontColor('#34445C')
      TextArea({ text: this.admissionText, placeholder: '\u7c98\u8d34\u5165\u9662\u8bb0\u5f55' })
        .onChange((value: string) => this.admissionText = value)
        .height(90).width('100%')
      Text('\u624b\u672f\u8bb0\u5f55').fontSize(13).fontColor('#34445C')
      TextArea({ text: this.surgeryText, placeholder: '\u7c98\u8d34\u624b\u672f\u8bb0\u5f55' })
        .onChange((value: string) => this.surgeryText = value)
        .height(90).width('100%')
      Button(this.busy ? '\u5904\u7406\u4e2d...' : '\u672c\u5730\u8131\u654f\u5e76\u521b\u5efa\u5ba1\u6838')
        .enabled(this.authenticated && !this.busy)
        .onClick(() => this.createReview())
        .width('100%').backgroundColor('#176B87')
      if (this.privacySummary.length > 0) {
        Text(this.privacySummary).fontSize(13).fontColor('#19715C')
      }
    }
    .alignItems(HorizontalAlign.Start)
    .width('100%')
    .padding(14)
    .backgroundColor(Color.White)
    .borderRadius(6)
  }

  @Builder
  taskPanel() {
    Column({ space: 9 }) {
      Text('\u5ba1\u6838\u5de5\u4f5c\u53f0').fontSize(16).fontWeight(FontWeight.Medium)
      Text(this.message).fontSize(14).fontColor('#34445C')
      if (this.task !== undefined) {
        Text(`ID: ${this.task.id}\n\u9636\u6bb5: ${this.task.status}  |  \u6a21\u5f0f: ${this.task.mode}`)
          .fontSize(13).fontColor('#5B6B7F')
        this.pendingAction()
        this.actionButtons()
      }
    }
    .alignItems(HorizontalAlign.Start)
    .width('100%')
    .padding(14)
    .backgroundColor(Color.White)
    .borderRadius(6)
  }

  @Builder
  reportPanel() {
    if (this.reportVisible) {
      Column({ space: 12 }) {
        Row() {
          Column({ space: 4 }) {
            Text('\u5ba1\u6838\u62a5\u544a').fontSize(18).fontWeight(FontWeight.Bold).fontColor('#172B4D')
            Text('\u57fa\u4e8e\u8131\u654f\u4efb\u52a1\u7684\u8d28\u91cf\u4e0e\u8bc1\u636e\u590d\u6838\u7ed3\u679c')
              .fontSize(13).fontColor('#5B6B7F')
          }
          .alignItems(HorizontalAlign.Start)
          Blank()
          Text(this.reportStatus === 'completed' ? '\u5df2\u5b8c\u6210' : this.reportStatus)
            .fontSize(13).fontColor('#19715C')
        }
        .width('100%')

        Row({ space: 8 }) {
          Column({ space: 4 }) {
            Text(this.reportQualityScore).fontSize(25).fontWeight(FontWeight.Bold).fontColor('#B54708')
            Text('\u8d28\u63a7\u8bc4\u5206').fontSize(12).fontColor('#5B6B7F')
          }
          .width('32%').padding(8).backgroundColor('#FFF7ED').borderRadius(4)
          Column({ space: 4 }) {
            Text(this.reportIssueCount).fontSize(25).fontWeight(FontWeight.Bold).fontColor('#B42318')
            Text('\u53d1\u73b0\u95ee\u9898').fontSize(12).fontColor('#5B6B7F')
          }
          .width('32%').padding(8).backgroundColor('#FEF3F2').borderRadius(4)
          Column({ space: 4 }) {
            Text(this.reportCriticalCount).fontSize(25).fontWeight(FontWeight.Bold).fontColor('#B42318')
            Text('\u4e25\u91cd\u95ee\u9898').fontSize(12).fontColor('#5B6B7F')
          }
          .width('32%').padding(8).backgroundColor('#FEF3F2').borderRadius(4)
        }
        .width('100%')
        .justifyContent(FlexAlign.SpaceBetween)
        Text('\u4e25\u91cd\u95ee\u9898 ' + this.reportCriticalCount + '  |  \u4e3b\u8981\u95ee\u9898 ' + this.reportMajorCount)
          .fontSize(12).fontColor('#5B6B7F').width('100%')

        Text('\u7f16\u7801\u7ed3\u8bba').fontSize(15).fontWeight(FontWeight.Medium).fontColor('#172B4D')
        Text('\u4e3b\u8981\u8bca\u65ad\uff1a' + this.reportPrimaryDiagnosis)
          .fontSize(13).fontColor('#34445C').width('100%')
        Text('\u624b\u672f\u7f16\u7801\uff1a' + this.reportProcedure)
          .fontSize(13).fontColor('#34445C').width('100%')
        Text('\u5206\u6790\u6a21\u5f0f\uff1a' + this.reportMode)
          .fontSize(13).fontColor('#34445C').width('100%')

        Text('\u8bc1\u636e\u590d\u6838').fontSize(15).fontWeight(FontWeight.Medium).fontColor('#172B4D')
        Text(this.reportEvidence).fontSize(13).fontColor('#A54200').width('100%')
        Text('\u4eba\u5de5\u51b3\u7b56\uff1a' + this.reportDecision)
          .fontSize(13).fontColor('#34445C').width('100%')

        Text('\u91cd\u70b9\u8d28\u63a7\u95ee\u9898').fontSize(15).fontWeight(FontWeight.Medium).fontColor('#172B4D')
        Text(this.reportIssues).fontSize(13).fontColor('#34445C').width('100%').maxLines(14)
        Text(this.reportRedaction).fontSize(12).fontColor('#5B6B7F').width('100%')
      }
      .alignItems(HorizontalAlign.Start)
      .width('100%')
      .padding(14)
      .backgroundColor(Color.White)
      .borderRadius(6)
    }
  }

  @Builder
  pendingAction() {
    if (this.hasOpenPendingAction()) {
      Text('\u53d1\u73b0\u8de8\u6587\u4e66\u4fa7\u522b\u51b2\u7a81\uff0c\u8bf7\u786e\u8ba4\u4f9d\u636e\u6765\u6e90\u3002')
        .fontSize(14).fontColor('#A54200')
      Row({ space: 8 }) {
        Button('\u4ee5\u5165\u9662\u8bb0\u5f55\u4e3a\u51c6')
          .onClick(() => this.confirmSource(this.openPendingActionId(), 'admission'))
          .backgroundColor('#B54708')
        Button('\u6807\u8bb0\u5f85\u8865\u5145')
          .onClick(() => this.markPending(this.openPendingActionId()))
          .backgroundColor('#667085')
      }
    }
  }

  @Builder
  actionButtons() {
    if (this.task !== undefined && ['created', 'extracted', 'coded', 'checked', 'recalculate'].includes(this.task.status)) {
      Button(this.task.status === 'recalculate' ? '\u5b8c\u6210\u4eba\u5de5\u786e\u8ba4\u540e\u91cd\u65b0\u8ba1\u7b97' : '\u81ea\u52a8\u6267\u884c\u5206\u6790\u6d41\u7a0b')
        .enabled(!this.busy)
        .onClick(() => this.runAutomaticAnalysis())
        .width('100%').backgroundColor('#176B87')
      Button('\u6267\u884c\u4e0b\u4e00\u6b65\u5ba1\u6838')
        .enabled(!this.busy)
        .onClick(() => this.advance())
        .width('100%').backgroundColor('#176B87')
    }
    if (this.task !== undefined && this.task.status === 'ready_for_confirmation') {
      Button('\u4eba\u5de5\u786e\u8ba4\u5e76\u5bfc\u51fa\u62a5\u544a')
        .enabled(!this.busy)
        .onClick(() => this.complete())
        .width('100%').backgroundColor('#176B87')
    }
      if (this.task !== undefined && ['completed', 'completed_with_pending'].includes(this.task.status)) {
        Button('\u67e5\u770b\u5ba1\u6838\u62a5\u544a')
          .enabled(!this.busy)
          .onClick(() => this.loadReport())
          .width('100%').backgroundColor('#176B87')
      Button('\u751f\u6210\u8de8\u8bbe\u5907\u7eed\u529e\u72b6\u6001')
        .onClick(() => this.message = ContinuationState.serialize(this.task as ReviewSnapshot))
        .width('100%').backgroundColor('#667085')
    }
  }

  @Builder
  timelinePanel() {
    Column({ space: 6 }) {
      Text('\u5ba1\u6838\u4e8b\u4ef6').fontSize(16).fontWeight(FontWeight.Medium)
      Text(this.timeline.length > 0 ? this.timeline : '\u4efb\u52a1\u5f00\u59cb\u540e\u8fd9\u91cc\u4f1a\u663e\u793a\u53ef\u590d\u6838\u7684\u8fd0\u884c\u8282\u70b9\u3002')
        .fontSize(13).fontColor('#5B6B7F').maxLines(12)
    }
    .alignItems(HorizontalAlign.Start)
    .width('100%')
    .padding(14)
    .backgroundColor(Color.White)
    .borderRadius(6)
  }

  private documents(): ReviewDocument[] {
    return [
      { id: 'admission', title: '\u5165\u9662\u8bb0\u5f55', record_type: 'admission', content: this.admissionText },
      { id: 'surgery', title: '\u624b\u672f\u8bb0\u5f55', record_type: 'surgery', content: this.surgeryText }
    ];
  }

  private openPendingActions(): Array<Record<string, Object>> {
    if (this.task === undefined) {
      return [];
    }
    return this.task.pending_actions.filter((action: Record<string, Object>) => String(action['status']) === 'open');
  }

  private hasOpenPendingAction(): boolean {
    return this.openPendingActions().length > 0;
  }

  private openPendingActionId(): string {
    const actions = this.openPendingActions();
    return actions.length > 0 ? String(actions[0]['id']) : '';
  }

  private gateway(): ReviewGateway {
    return new ReviewGateway(this.endpoint.trim(), this.token.trim());
  }

  private errorText(error: Object): string {
    const value = error as Record<string, Object>;
    const message = value['message'];
    if (message !== undefined) {
      return String(message);
    }
    const serialized = JSON.stringify(error);
    return serialized === undefined ? String(error) : serialized;
  }

  private changeEndpoint(value: string): void {
    this.endpoint = value;
    this.authenticated = false;
    this.token = '';
  }

  private async login(): Promise<void> {
    if (this.endpoint.trim().length === 0 || this.username.trim().length === 0 || this.password.length === 0) {
      this.message = '\u8bf7\u586b\u5199\u5185\u7f51\u5730\u5740\u3001\u8d26\u53f7\u548c\u5bc6\u7801\u3002';
      return;
    }
    try {
      this.busy = true;
      const session = await new AuthGateway(this.endpoint.trim()).login(this.username.trim(), this.password);
      this.token = session.access_token;
      this.authenticated = true;
      this.password = '';
      this.message = '\u8fde\u63a5\u6210\u529f\uff0c\u53ef\u5f00\u59cb\u672c\u5730\u8131\u654f\u5ba1\u6838\u3002';
    } catch (error) {
      this.authenticated = false;
      this.token = '';
      this.message = `\u767b\u5f55\u5931\u8d25: ${this.errorText(error)}`;
    } finally {
      this.busy = false;
    }
  }

  private async createReview(): Promise<void> {
    if (!this.authenticated || this.token.trim().length === 0) {
      this.message = '\u8bf7\u5148\u767b\u5f55\u5185\u7f51\u3002';
      return;
    }
    try {
      this.busy = true;
      const local = new LocalPrivacyGate().redact(this.documents());
      this.privacySummary = `\u672c\u5730\u8131\u654f\u5df2\u5904\u7406 ${local.receipt.redacted_count} \u9879\uff1a${local.receipt.categories.join(', ') || '\u65e0'}`;
      this.task = await this.gateway().create(local.documents, local.receipt);
      this.message = '\u5ba1\u6838\u4efb\u52a1\u5df2\u521b\u5efa\uff0c\u8bf7\u6267\u884c\u4e0b\u4e00\u6b65\u3002';
      await this.refreshEvents();
    } catch (error) {
      this.message = `\u521b\u5efa\u5931\u8d25: ${this.errorText(error)}`;
    } finally {
      this.busy = false;
    }
  }

  private async advance(): Promise<void> {
    if (this.task === undefined) return;
      try {
        this.busy = true;
        this.task = await this.gateway().advance(this.task);
        this.message = `\u5df2\u63a8\u8fdb\u5230 ${this.task.status}`;
        await this.refreshEvents();
      } catch (error) {
        const detail = this.errorText(error);
        if (detail.includes('(409)')) {
          try {
            this.task = await this.gateway().get(this.task.id);
            await this.refreshEvents();
            this.message = `\u4efb\u52a1\u72b6\u6001\u5df2\u5237\u65b0\u5230 ${this.task.status}\uff0c\u53ef\u7ee7\u7eed\u5206\u6790\u3002`;
          } catch (refreshError) {
            this.message = `\u5237\u65b0\u4efb\u52a1\u5931\u8d25: ${this.errorText(refreshError)}`;
          }
        } else {
          this.message = `\u5904\u7406\u5931\u8d25: ${detail}`;
        }
      } finally {
        this.busy = false;
      }
  }

  private async runAutomaticAnalysis(): Promise<void> {
    if (this.task === undefined) return;
    try {
      this.busy = true;
      while (['created', 'extracted', 'coded', 'checked', 'recalculate'].includes(this.task.status)) {
        this.task = await this.gateway().advance(this.task);
        await this.refreshEvents();
        if (this.task.status === 'waiting_for_human' || this.task.status === 'ready_for_confirmation') {
          break;
        }
      }
      this.message = this.task.status === 'waiting_for_human'
        ? '\u5206\u6790\u5df2\u6682\u505c\uff0c\u8bf7\u4eba\u5de5\u786e\u8ba4\u8bc1\u636e\u6765\u6e90\u3002'
        : `\u5206\u6790\u5df2\u5b8c\u6210\uff0c\u5f53\u524d\u9636\u6bb5\uff1a${this.task.status}`;
    } catch (error) {
      this.message = `\u81ea\u52a8\u5206\u6790\u5931\u8d25: ${this.errorText(error)}`;
    } finally {
      this.busy = false;
    }
  }

  private async confirmSource(issueId: string, documentId: string): Promise<void> {
    if (this.task === undefined) return;
    try {
      this.busy = true;
      this.task = await this.gateway().confirmSource(this.task, issueId, documentId, '\u7f16\u7801\u5458\u5df2\u786e\u8ba4\u4f9d\u636e\u6765\u6e90');
      this.message = '\u4f9d\u636e\u5df2\u786e\u8ba4\uff0c\u8bf7\u91cd\u65b0\u8ba1\u7b97\u7f16\u7801\u5efa\u8bae\u3002';
      await this.refreshEvents();
    } catch (error) {
      this.message = `\u786e\u8ba4\u5931\u8d25: ${this.errorText(error)}`;
    } finally {
      this.busy = false;
    }
  }

  private async markPending(issueId: string): Promise<void> {
    if (this.task === undefined) return;
    try {
      this.busy = true;
      this.task = await this.gateway().markPending(this.task, issueId, '\u7b49\u5f85\u8865\u5145\u539f\u59cb\u8bc1\u636e');
      this.message = '\u8be5\u8bc1\u636e\u5df2\u6807\u8bb0\u5f85\u8865\u5145\uff0c\u53ef\u4ee5\u7ee7\u7eed\u4eba\u5de5\u786e\u8ba4\u3002';
      await this.refreshEvents();
    } catch (error) {
      this.message = `\u6807\u8bb0\u5931\u8d25: ${this.errorText(error)}`;
    } finally {
      this.busy = false;
    }
  }

  private async complete(): Promise<void> {
    if (this.task === undefined) return;
    try {
      this.busy = true;
      this.task = await this.gateway().complete(this.task);
      await this.loadReport();
      await this.refreshEvents();
    } catch (error) {
      this.message = `\u5b8c\u6210\u5931\u8d25: ${this.errorText(error)}`;
    } finally {
      this.busy = false;
    }
  }

  private async refreshEvents(): Promise<void> {
    if (this.task === undefined) return;
    const events = await this.gateway().events(this.task);
    this.timeline = events.map((event) => `${event.sequence}. ${event.phase}: ${event.event_type}`).join('\n');
  }

  private valueText(value: Object | undefined, fallback: string): string {
    if (value === undefined) {
      return fallback;
    }
    const text = String(value);
    return text === 'null' ? fallback : text;
  }

  private severityText(value: Object | undefined): string {
    const severity = this.valueText(value, '\u63d0\u793a');
    if (severity === 'critical') {
      return '\u4e25\u91cd';
    }
    if (severity === 'major') {
      return '\u4e3b\u8981';
    }
    if (severity === 'minor') {
      return '\u4e00\u822c';
    }
    return severity;
  }

  private actionText(value: Object | undefined): string {
    const action = this.valueText(value, '\u672a\u77e5\u64cd\u4f5c');
    if (action === 'confirm_source') {
      return '\u786e\u8ba4\u8bc1\u636e\u6765\u6e90';
    }
    if (action === 'confirm_review') {
      return '\u786e\u8ba4\u5b8c\u6210\u5ba1\u6838';
    }
    return action;
  }

  private applyReport(report: Record<string, Object>): void {
    this.reportVisible = true;
    this.reportStatus = this.valueText(report['status'], '\u672a\u77e5');
    this.reportMode = this.valueText(report['mode'], '\u672a\u77e5');
    const emptyObject: Record<string, Object> = {};

    const codingValue = report['coding'];
    const coding = codingValue === undefined ? emptyObject : codingValue as Record<string, Object>;
    const primaryValue = coding['primary_diagnosis'];
    if (primaryValue === undefined || String(primaryValue) === 'null') {
      this.reportPrimaryDiagnosis = '\u5f85\u8865\u5145\uff1a\u672a\u68c0\u51fa\u660e\u786e\u4e3b\u8bca\u65ad';
    } else {
      const primary = primaryValue as Record<string, Object>;
      this.reportPrimaryDiagnosis = this.valueText(primary['code'], '') + ' ' +
        this.valueText(primary['name'], '\u672a\u547d\u540d');
    }

    const proceduresValue = coding['procedures'];
    const procedures = proceduresValue === undefined ? [] : proceduresValue as Array<Record<string, Object>>;
    if (procedures.length > 0) {
      const procedure = procedures[0];
      this.reportProcedure = this.valueText(procedure['code'], '') + ' ' +
        this.valueText(procedure['name'], '\u672a\u547d\u540d') + ' (' +
        this.valueText(procedure['confidence'], '\u65e0\u7f6e\u4fe1\u5ea6') + ')';
    } else {
      this.reportProcedure = '\u672a\u68c0\u51fa\u624b\u672f\u7f16\u7801';
    }

    const qualityValue = report['quality'];
    const quality = qualityValue === undefined ? emptyObject : qualityValue as Record<string, Object>;
    this.reportQualityScore = this.valueText(quality['qc_score'], '--') + ' / 100';
    this.reportIssueCount = this.valueText(quality['total_issues'], '0');
    this.reportCriticalCount = this.valueText(quality['critical_count'], '0');
    this.reportMajorCount = this.valueText(quality['major_count'], '0');

    const issuesValue = quality['issues'];
    const issues = issuesValue === undefined ? [] : issuesValue as Array<Record<string, Object>>;
    if (issues.length === 0) {
      this.reportIssues = '\u6682\u65e0\u8d28\u63a7\u95ee\u9898\u3002';
    } else {
      this.reportIssues = issues.map((issue: Record<string, Object>, index: number) => {
        const severity = this.severityText(issue['severity']);
        const name = this.valueText(issue['rule_name'], '\u672a\u547d\u540d\u89c4\u5219');
        const description = this.valueText(issue['description'], '\u65e0\u63cf\u8ff0');
        const suggestion = this.valueText(issue['suggestion'], '\u8bf7\u4eba\u5de5\u6838\u5b9e');
        return (index + 1) + '. [' + severity + '] ' + name + '\n' + description + '\n\u5efa\u8bae\uff1a' + suggestion;
      }).join('\n\n');
    }

    const evidenceValue = report['evidence'];
    const evidence = evidenceValue === undefined ? emptyObject : evidenceValue as Record<string, Object>;
    const conflictsValue = evidence['conflicts'];
    const conflicts = conflictsValue === undefined ? [] : conflictsValue as Array<Record<string, Object>>;
    if (conflicts.length > 0) {
      const conflict = conflicts[0];
      const title = this.valueText(conflict['title'], '\u8bc1\u636e\u4e0d\u4e00\u81f4');
      const displayTitle = title.includes('laterality') ? '\u8de8\u6587\u4e66\u4fa7\u522b\u51b2\u7a81' : title;
      this.reportEvidence = '\u53d1\u73b0 ' + conflicts.length + ' \u4e2a\u8de8\u6587\u4e66\u8bc1\u636e\u51b2\u7a81\uff1a' +
        displayTitle + '\u3002\u5df2\u8fdb\u5165\u4eba\u5de5\u590d\u6838\u3002';
    } else {
      this.reportEvidence = '\u672a\u53d1\u73b0\u8de8\u6587\u4e66\u8bc1\u636e\u51b2\u7a81\u3002';
    }

    const decisionsValue = report['decisions'];
    const decisions = decisionsValue === undefined ? [] : decisionsValue as Array<Record<string, Object>>;
    if (decisions.length > 0) {
      this.reportDecision = '\u5df2\u8bb0\u5f55 ' + decisions.length + ' \u9879\u4eba\u5de5\u51b3\u7b56\uff1a' +
        decisions.map((decision: Record<string, Object>) => this.actionText(decision['action'])).join('\u3001');
    } else {
      this.reportDecision = '\u6682\u65e0\u4eba\u5de5\u51b3\u7b56\u3002';
    }

    const receiptValue = report['redaction_receipt'];
    const receipt = receiptValue === undefined ? emptyObject : receiptValue as Record<string, Object>;
    this.reportRedaction = '\u672c\u5730\u8131\u654f\u5df2\u5904\u7406 ' + this.valueText(receipt['redacted_count'], '0') + ' \u9879\u3002';
  }

  private async loadReport(): Promise<void> {
    if (this.task === undefined) return;
    try {
      this.busy = true;
      this.message = '\u6b63\u5728\u52a0\u8f7d\u5ba1\u6838\u62a5\u544a...';
      const report = await this.gateway().report(this.task);
      this.applyReport(report);
      this.message = '\u5ba1\u6838\u62a5\u544a\u5df2\u751f\u6210\uff0c\u4ec5\u5305\u542b\u8131\u654f\u4efb\u52a1\u6570\u636e\u3002';
    } catch (error) {
      this.message = '\u67e5\u770b\u62a5\u544a\u5931\u8d25: ' + this.errorText(error);
    } finally {
      this.busy = false;
    }
  }
}
