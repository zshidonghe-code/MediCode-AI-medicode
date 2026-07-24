import { ReviewDocument, ReviewSnapshot } from '../model/ReviewModels';
import { ContinuationState } from '../service/ContinuationState';
import { LocalPrivacyGate } from '../service/LocalPrivacyGate';
import { ReviewGateway } from '../service/ReviewGateway';

const LEFT_FRACTURE = '\u5de6\u4fa7\u80a1\u9aa8\u9888\u9aa8\u6298\uff0c\u8be6\u89c1\u5165\u9662\u8bb0\u5f55\u3002';
const RIGHT_SURGERY = '\u53f3\u4fa7\u5168\u9acb\u5173\u8282\u7f6e\u6362\u672f\u5df2\u5b8c\u6210\u3002';

@Entry
@Component
struct Index {
  @State endpoint: string = 'http://127.0.0.1:8000';
  @State token: string = '';
  @State admissionText: string = LEFT_FRACTURE;
  @State surgeryText: string = RIGHT_SURGERY;
  @State task: ReviewSnapshot | undefined = undefined;
  @State message: string = '\u5c1a\u672a\u521b\u5efa\u5ba1\u6838\u4efb\u52a1';
  @State privacySummary: string = '';
  @State timeline: string = '';
  @State report: string = '';
  @State busy: boolean = false;

  build() {
    Scroll() {
      Column({ space: 14 }) {
        this.header()
        this.connectionPanel()
        this.documentPanel()
        this.taskPanel()
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
        .onChange((value: string) => this.endpoint = value)
        .width('100%')
      TextInput({ text: this.token, placeholder: '\u8fd0\u8425\u5458\u767b\u5f55 Token' })
        .type(InputType.Password)
        .onChange((value: string) => this.token = value)
        .width('100%')
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
        .enabled(!this.busy)
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
      if (this.report.length > 0) {
        Text(this.report).fontSize(12).fontColor('#34445C').maxLines(8)
      }
    }
    .alignItems(HorizontalAlign.Start)
    .width('100%')
    .padding(14)
    .backgroundColor(Color.White)
    .borderRadius(6)
  }

  @Builder
  pendingAction() {
    if (this.task !== undefined && this.task.pending_actions.length > 0) {
      const action = this.task.pending_actions[0];
      Text('\u53d1\u73b0\u8de8\u6587\u4e66\u4fa7\u522b\u51b2\u7a81\uff0c\u8bf7\u786e\u8ba4\u4f9d\u636e\u6765\u6e90\u3002')
        .fontSize(14).fontColor('#A54200')
      Row({ space: 8 }) {
        Button('\u4ee5\u5165\u9662\u8bb0\u5f55\u4e3a\u51c6')
          .onClick(() => this.confirmSource(String(action['id']), 'admission'))
          .backgroundColor('#B54708')
        Button('\u6807\u8bb0\u5f85\u8865\u5145')
          .onClick(() => this.markPending(String(action['id'])))
          .backgroundColor('#667085')
      }
    }
  }

  @Builder
  actionButtons() {
    if (this.task !== undefined && ['created', 'extracted', 'coded', 'checked', 'recalculate'].includes(this.task.status)) {
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

  private gateway(): ReviewGateway {
    return new ReviewGateway(this.endpoint.trim(), this.token.trim());
  }

  private async createReview(): Promise<void> {
    if (this.endpoint.trim().length === 0 || this.token.trim().length === 0) {
      this.message = '\u8bf7\u5148\u586b\u5199\u5185\u7f51\u5730\u5740\u548c\u8fd0\u8425\u5458 Token\u3002';
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
      this.message = `\u521b\u5efa\u5931\u8d25: ${String(error)}`;
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
      this.message = `\u5904\u7406\u5931\u8d25: ${String(error)}`;
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
      this.message = `\u786e\u8ba4\u5931\u8d25: ${String(error)}`;
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
      this.message = `\u6807\u8bb0\u5931\u8d25: ${String(error)}`;
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
      this.message = `\u5b8c\u6210\u5931\u8d25: ${String(error)}`;
    } finally {
      this.busy = false;
    }
  }

  private async refreshEvents(): Promise<void> {
    if (this.task === undefined) return;
    const events = await this.gateway().events(this.task);
    this.timeline = events.map((event) => `${event.sequence}. ${event.phase}: ${event.event_type}`).join('\n');
  }

  private async loadReport(): Promise<void> {
    if (this.task === undefined) return;
    const report = await this.gateway().report(this.task);
    this.report = JSON.stringify(report, null, 2);
    this.message = '\u5ba1\u6838\u62a5\u544a\u5df2\u751f\u6210\uff0c\u4ec5\u5305\u542b\u8131\u654f\u4efb\u52a1\u6570\u636e\u3002';
  }
}
