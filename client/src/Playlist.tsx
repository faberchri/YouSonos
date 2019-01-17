import React from "react";
import {changePlaylistTrackPosition, playlistChanged, Track, PlaylistItem} from "./api";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import List from '@material-ui/core/List';
import DragHandleRounded from '@material-ui/icons/DragHandleRounded';
import {arrayMove, SortableContainer, SortableElement, SortableHandle, SortEnd, SortEvent} from 'react-sortable-hoc';
import PlaylistEntry from "./PlaylistEntry";

interface State {
    playlistItems: PlaylistItem[];
}

const styles = (theme: Theme) => createStyles({
    list: {
        overflow: 'auto'
    }
});

interface Props extends WithStyles<typeof styles> {}

const DragHandleInstance = SortableHandle(() => <DragHandleRounded/>);

const SortableItem = SortableElement(({playlistItem, playlistIndex}: {playlistItem: PlaylistItem, playlistIndex: number}) =>{
    return(
        <PlaylistEntry playlistItem={playlistItem} playlistIndex={playlistIndex}/>
    );
});

const SortableList = SortableContainer(({playlistItems, classNames}: {playlistItems: PlaylistItem[], classNames: string}) => {
    return (

        <List dense className={classNames}>
            {playlistItems.map((value, index) => (
                <SortableItem key={`item-${index}`} index={index} playlistItem={value} playlistIndex={index} />
            ))}
        </List>

    );
});

class Playlist extends React.Component<Props, State> {

    constructor(props: Props) {
        super(props);
        this.setPlaylist = this.setPlaylist.bind(this);
        this.onSortEnd = this.onSortEnd.bind(this);

        this.state = {playlistItems: []};
    }

    componentDidMount() {
        playlistChanged(this.setPlaylist)
    }

    setPlaylist(data: PlaylistItem[]) {
        this.setState({playlistItems: data });
    }

    onSortEnd (sort: SortEnd, event: SortEvent){
        const movedEntry = this.state.playlistItems[sort.oldIndex];
        this.setState({
            playlistItems: arrayMove(this.state.playlistItems, sort.oldIndex, sort.newIndex),
        });
        changePlaylistTrackPosition(movedEntry.playlist_entry_id, sort.newIndex)
    };

    render() {
        const { classes } = this.props;

        return (
            <SortableList playlistItems={this.state.playlistItems}
                          classNames={classes.list}
                          onSortEnd={this.onSortEnd}
                          useDragHandle={true}
                          lockAxis={'y'} />
        );
    }
}
export default withStyles(styles) (Playlist);
